# Ghostty Discord Bot

The Ghostty Discord Bot, humorlessly named "Ghostty Bot."

## Development

The Nix environment is the only supported development environment. You can
develp this without Nix, of course, but I'm not going to help you figure it
out.

Once your environment is setup, create a `.env` file based on `.env.example`
and run the app:

```
$ python -m app
...
```

You will have to setup a Discord bot and get a Discord bot token. The
instructions for that are out of scope for this README. The Discord bot
will require the following privileges:

  - Manage Roles
  - Members Privileged Intents

