package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"github.com/joho/godotenv"
	"github.com/slack-go/slack"
	"github.com/slack-go/slack/slackevents"
)

var (
	slackBotToken      string
	slackSigningSecret string
	pythonAPIURL       string
	port               string
)

func init() {
	godotenv.Load("../../.env")

	slackBotToken = os.Getenv("SLACK_BOT_TOKEN")
	slackSigningSecret = os.Getenv("SLACK_SIGNING_SECRET")
	pythonAPIURL = os.Getenv("PYTHON_API_URL")
	port = os.Getenv("SLACK_BOT_PORT")

	if port == "" {
		port = "3000"
	}

	if slackBotToken == "" || slackSigningSecret == "" {
		log.Fatal("SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET must be set")
	}

	log.Printf("Slack Bot initialized - Port: %s", port)
}

func HandleEvents(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	sv, err := slack.NewSecretsVerifier(r.Header, slackSigningSecret)
	if err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	if _, err := sv.Write(body); err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	if err := sv.Ensure(); err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	eventsAPIEvent, err := slackevents.ParseEvent(json.RawMessage(body), slackevents.OptionNoVerifyToken())
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	if eventsAPIEvent.Type == slackevents.URLVerification {
		var r *slackevents.ChallengeResponse
		err := json.Unmarshal([]byte(body), &r)
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text")
		w.Write([]byte(r.Challenge))
		return
	}

	if eventsAPIEvent.Type == slackevents.CallbackEvent {
		innerEvent := eventsAPIEvent.InnerEvent
		switch ev := innerEvent.Data.(type) {
		case *slackevents.MessageEvent:
			HandleMessage(ev)
		case *slackevents.AppMentionEvent:
			HandleMention(ev)
		}
	}

	w.WriteHeader(http.StatusOK)
}

func HandleMessage(event *slackevents.MessageEvent) {
	client := slack.New(slackBotToken)
	response := fmt.Sprintf("Echo: %s", event.Text)

	_, _, err := client.PostMessage(
		event.Channel,
		slack.MsgOptionText(response, false),
	)
	if err != nil {
		log.Printf("Error posting message: %v", err)
	}
}

func HandleMention(event *slackevents.AppMentionEvent) {
	client := slack.New(slackBotToken)
	response := fmt.Sprintf("Hi <@%s>! You mentioned me. Echo: %s", event.User, event.Text)

	_, _, err := client.PostMessage(
		event.Channel,
		slack.MsgOptionText(response, false),
	)
	if err != nil {
		log.Printf("Error posting mention response: %v", err)
	}
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

	sv, err := slack.NewSecretsVerifier(r.Header, slackSigningSecret)
	if err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	if _, err := sv.Write(body); err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	if err := sv.Ensure(); err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	s, err := slack.SlashCommandParse(body)
	if err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		return
	}

	response := slack.SlashCommandResponse{
		ResponseType: slack.ResponseTypeInChannel,
		Text:         fmt.Sprintf("Command received: `%s` with text: `%s`", s.Command, s.Text),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func HandleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status": "ok",
		"service": "slack-bot",
	})
}

func main() {
	http.HandleFunc("/slack/events", HandleEvents)
	http.HandleFunc("/slack/commands", HandleCommand)
	http.HandleFunc("/health", HandleHealth)

	log.Printf("Slack Bot listening on port %s", port)
	if err := http.ListenAndServe(fmt.Sprintf(":%s", port), nil); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
