package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/joho/godotenv"
	"github.com/slack-go/slack"
	"github.com/slack-go/slack/slackevents"
)

var (
	slackBotToken      string
	slackSigningSecret string
	pythonAPIURL       string
	port               string
	botUserID          string
	mentionPattern     *regexp.Regexp
	httpClient         = &http.Client{Timeout: 90 * time.Second}
)

func init() {
	godotenv.Load("../../.env")

	slackBotToken = os.Getenv("SLACK_BOT_TOKEN")
	slackSigningSecret = os.Getenv("SLACK_SIGNING_SECRET")
	pythonAPIURL = strings.TrimRight(os.Getenv("PYTHON_API_URL"), "/")
	port = os.Getenv("SLACK_BOT_PORT")
	if port == "" {
		port = os.Getenv("PORT")
	}
	if port == "" {
		port = "3000"
	}
	if pythonAPIURL == "" {
		pythonAPIURL = "http://localhost:8000"
	}
	if slackBotToken == "" || slackSigningSecret == "" {
		log.Fatal("SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET must be set")
	}

	api := slack.New(slackBotToken)
	identity, err := api.AuthTest()
	if err != nil {
		log.Fatalf("Slack auth.test failed: %v", err)
	}
	botUserID = identity.UserID
	mentionPattern = regexp.MustCompile(fmt.Sprintf(`<@%s>`, regexp.QuoteMeta(botUserID)))
	log.Printf("Slack Bot initialized as %s (%s) on port %s", identity.User, botUserID, port)
}

func HandleEvents(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}
	if err := verifySlackSignature(r.Header, body); err != nil {
		log.Printf("event signature check failed: %v", err)
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	eventsAPIEvent, err := slackevents.ParseEvent(json.RawMessage(body), slackevents.OptionNoVerifyToken())
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	if eventsAPIEvent.Type == slackevents.URLVerification {
		var challenge slackevents.ChallengeResponse
		if err := json.Unmarshal(body, &challenge); err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(challenge.Challenge))
		return
	}

	w.WriteHeader(http.StatusOK)
	if eventsAPIEvent.Type != slackevents.CallbackEvent {
		return
	}

	go func() {
		switch ev := eventsAPIEvent.InnerEvent.Data.(type) {
		case *slackevents.MessageEvent:
			handleMessage(ev)
		case *slackevents.AppMentionEvent:
			handleMention(ev)
		}
	}()
}

func handleMessage(event *slackevents.MessageEvent) {
	if shouldIgnoreMessage(event.BotID, event.User, event.SubType, event.Text) {
		return
	}

	ingest(event.Channel, event.TimeStamp, event.ThreadTimeStamp, event.User, event.Text, event.ChannelType)

	// Channel @mentions are handled by app_mention. Answer here only for DMs
	// that did not also include an @mention, so we do not double-reply.
	if isDirectMessage(event.Channel, event.ChannelType) && !mentionPattern.MatchString(event.Text) {
		answerAndReply(event.Channel, event.User, event.Text, event.ChannelType)
	}
}

func handleMention(event *slackevents.AppMentionEvent) {
	if shouldIgnoreMessage("", event.User, "", event.Text) {
		return
	}
	ingest(event.Channel, event.TimeStamp, event.ThreadTimeStamp, event.User, event.Text, "channel")
	question := mentionPattern.ReplaceAllString(event.Text, "")
	answerAndReply(event.Channel, event.User, strings.TrimSpace(question), "channel")
}

func HandleCommand(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	body, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}
	if err := verifySlackSignature(r.Header, body); err != nil {
		log.Printf("slash command signature check failed: %v", err)
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	r.Body = io.NopCloser(bytes.NewBuffer(body))
	s, err := slack.SlashCommandParse(r)
	if err != nil {
		log.Printf("slash command parse failed: %v", err)
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	w.WriteHeader(http.StatusOK)
	go func() {
		question := strings.TrimSpace(s.Text)
		if question == "" {
			question = "What should I focus on from recent Slack history?"
		}
		ingest(s.ChannelID, fmt.Sprintf("%d.000000", time.Now().Unix()), "", s.UserID, question, "command")
		answerAndReply(s.ChannelID, s.UserID, question, "command")
	}()
}

func shouldIgnoreMessage(botID, user, subtype, text string) bool {
	if botID != "" || user == botUserID {
		return true
	}
	if subtype != "" && subtype != "file_share" {
		return true
	}
	return strings.TrimSpace(text) == ""
}

func isDirectMessage(channelID, channelType string) bool {
	return channelType == "im" || strings.HasPrefix(channelID, "D")
}

func ingest(channelID, ts, threadTS, userID, text, channelType string) {
	payload := map[string]string{
		"channel_id":   channelID,
		"ts":           ts,
		"thread_ts":    threadTS,
		"user_id":      userID,
		"text":         text,
		"channel_type": channelType,
	}
	if err := postJSON("/history/ingest", payload, 8*time.Second); err != nil {
		log.Printf("history ingest failed: %v", err)
	}
}

func answerAndReply(channelID, userID, question, channelType string) {
	question = strings.TrimSpace(question)
	if question == "" {
		question = "What should I do based on recent Slack history?"
	}
	log.Printf("answering %s in %s (%s)", userID, channelID, channelType)

	body := map[string]string{
		"text":         question,
		"channel_id":   channelID,
		"channel_type": channelType,
		"user_id":      userID,
	}
	response, err := askPython(body)
	if err != nil {
		log.Printf("ask failed: %v", err)
		response = "I could not answer from chat history right now. Check that the Python API is running and CLAUDE_API_KEY is set."
	}
	reply(channelID, response)
}

func askPython(payload map[string]string) (string, error) {
	raw, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	req, err := http.NewRequest(http.MethodPost, pythonAPIURL+"/ask", bytes.NewReader(raw))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	out, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	if resp.StatusCode >= 300 {
		return "", fmt.Errorf("python api status %d: %s", resp.StatusCode, out)
	}
	var parsed struct {
		Response string `json:"response"`
	}
	if err := json.Unmarshal(out, &parsed); err != nil {
		return "", err
	}
	return parsed.Response, nil
}

func postJSON(path string, payload map[string]string, timeout time.Duration) error {
	raw, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	req, err := http.NewRequest(http.MethodPost, pythonAPIURL+path, bytes.NewReader(raw))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: timeout}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("status %d: %s", resp.StatusCode, body)
	}
	return nil
}

func reply(channelID, text string) {
	if len(text) > 3500 {
		text = text[:3500] + "\n…"
	}
	api := slack.New(slackBotToken)
	_, _, err := api.PostMessage(channelID, slack.MsgOptionText(text, false))
	if err != nil {
		log.Printf("error posting to %s: %v", channelID, err)
	}
}

func verifySlackSignature(header http.Header, body []byte) error {
	sv, err := slack.NewSecretsVerifier(header, slackSigningSecret)
	if err != nil {
		return err
	}
	if _, err := sv.Write(body); err != nil {
		return err
	}
	return sv.Ensure()
}

func HandleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"service": "slack-bot",
		"bot":     botUserID,
	})
}

func logRequest(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log.Printf("%s %s", r.Method, r.URL.Path)
		next(w, r)
	}
}

func main() {
	http.HandleFunc("/slack/events", logRequest(HandleEvents))
	http.HandleFunc("/slack/commands", logRequest(HandleCommand))
	http.HandleFunc("/health", logRequest(HandleHealth))

	log.Printf("Slack Bot listening on port %s", port)
	if err := http.ListenAndServe(fmt.Sprintf(":%s", port), nil); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
