## Why

A production bot that runs group games in forum topics vendors the toolkit for
end-to-end tests. It found places where the fake is kinder than Telegram, in ways its
own code can observe:

- **Topic errors are the toolkit's own words.** A call into an unknown thread fails with
  "Topic N does not exist in chat X". Bots match Telegram's texts, so their `except`
  branches never ran.
- **Closed topics are open.** A bot that is a plain member posts into a closed topic, and
  into a closed or hidden General topic. Telegram answers `TOPIC_CLOSED`.
- **Topic messages have no root.** In Telegram a topic message that replies to nothing
  else carries the topic's `forum_topic_created` message as `reply_to_message`. Bots read
  the topic's name from it, and here it was `None`.
- **The bot holds every right.** A bot declared as a plain member pins, deletes others'
  messages, bans, restricts and promotes, and sends what the chat's permissions forbid.
  Telegram refuses each of those, so a bot's "I lack the right" branch went untested.
