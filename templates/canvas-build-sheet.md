# Canvas build sheet: {{project_name}}

Built {{built}} by shotcraft. Use case: {{use_case}}. Delivery: {{delivery}}.

This sheet rebuilds the project in Higgsfield Canvas (the node board), one group of nodes per shot. Every
input is already uploaded to Higgsfield where an upload id is shown, so in Canvas you pick it from your
uploads instead of uploading it again. Prompts are final: paste them as they are.

{{canvas_api_note}}

## How to read this sheet

- **Input nodes**: pictures, clips or audio that feed the model (start frame, end frame, references). Each
  one names the file in the project, its upload id, and the port it connects to on the model node.
- **Prompt node**: a text node. Paste the text exactly.
- **Model node**: the model to pick and its settings (aspect, resolution, duration, audio).
- **Edges**: which node connects to which port.
- **Final output**: the approved result shotcraft already made. Keep it on the board as the target to match,
  or as the start of the next step (upscale, edit).

Build order for each shot: add the input nodes, then the prompt node, then the model node; connect the
edges; set the model settings; check the cost Canvas shows before you run anything. Running a node in
Canvas spends credits again: the approved result below already exists, so only re-run when you want a
new take.

## Uploads

{{upload_summary}}

{{upload_table}}

{{skipped}}

## Shots

{{shots}}

## After the build

- Name each node group after its shot id (S010, S020 ...) so the board matches the shot list.
- Put the groups left to right in shot-list order.
- If something on this sheet does not match what Canvas offers (a model renamed, a setting missing), note it
  and tell Claude: it goes into the lessons inbox so the next sheet is right.
