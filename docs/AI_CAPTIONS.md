# Automatic Instagram Reel captions with Gemini

Autogram can create a caption for a Reel by analysing the actual video with
Google Gemini. It uses the video bytes, not the filename.

## How it works

- The feature runs only for a Reel whose `post.md` caption is blank.
- A caption already written by you is never replaced.
- Gemini analyses the video and its audio, then returns a caption with relevant
  hashtags.
- The caption is passed directly to Instagram when the Reel is published.
- If Gemini cannot process the video or return a caption, the post is not
  published. An `error.txt` is written into that post's folder so it can be
  fixed and retried.
- The temporary upload to Gemini is deleted after the request where possible.

## GitHub setup

Add a repository Actions secret named `GEMINI_API_KEY` containing your key
from Google AI Studio. The publish workflow passes this secret to the program;
never put the key in a source file or in Google Drive.

The model can be changed by setting the optional `GEMINI_MODEL` environment
variable. The default is `gemini-3.8-flash`.

## Using it

For automatic captions, leave the body of `post.md` empty. For example:

```markdown
---
type: reel
---
```

To use your own caption, simply write it below the front matter. Gemini will
not overwrite it.

The caption is generated during the actual publishing run, not during a
dry-run preview. A working Instagram configuration and the existing Autogram
storage setup are still required.
