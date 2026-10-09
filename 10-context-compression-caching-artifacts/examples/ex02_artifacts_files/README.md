# Example 02 — Files in and out

Upload an image → multimodal describe → save the caption as an artifact → recall it in a
later turn with `LoadArtifactsTool`.

```powershell
python run.py
```

## Captured output

```
(uploading a 83-byte PNG)

user> What's in this image?  [+image]
  [call] save_caption({'caption': 'This image is a solid blue color.'})
agent> The image shows a solid blue color.

user> Remind me what that image showed.
  [call] load_artifacts({'artifact_names': ['caption.txt']})
agent> The image showed a solid blue color.

artifacts: ['caption.txt']
```

## Takeaways

- An uploaded file is just another `types.Part` in the message:
  ```python
  types.Content(role="user", parts=[
      types.Part(text="What's in this image?"),
      types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
  ])
  ```
- `run.py` includes a ~40-line pure-Python PNG encoder so the example needs no image file
  or Pillow.
- The agent generated a caption and stored it (`save_artifact` → `caption.txt`).
- Turn 2 has no image; `LoadArtifactsTool()` lets the model pull `caption.txt` back
  (`load_artifacts({'artifact_names': [...]})`).
- Prod alternative to the manual save: `RunConfig(save_input_blobs_as_artifacts=True)`
  auto-stores every uploaded blob.
