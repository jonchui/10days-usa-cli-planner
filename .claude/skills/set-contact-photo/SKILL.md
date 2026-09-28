---
name: "set-contact-photo"
description: "Put a photo on someone's card in JC's macOS Contacts: take an image from the clipboard, an attached picture, a screenshot, or an iMessage thread, crop it to a square headshot of the right person, and save it as that contact's photo. Use whenever JC says contact photo, contact image, contact pic, 'store into X's contact', 'add this picture to X', 'turn clipboard into image then contact', or is creating a contact and wants the photo set, even if he doesn't say the word photo."
---

# Set contact photo

JC often meets someone, gets their name over iMessage, and wants their face on the contact card while the card is still open. This skill takes an image from wherever it lives, crops it to the right person, and saves it into Contacts on JC's Mac. It runs end to end without asking JC anything he already said.

Everything here is reversible (a contact photo can be replaced in one click), so act first and report after.

## Recover inputs before doing anything

| Input | Where to find it |
|---|---|
| Person's name | JC's message ("Durzo's contact"). Match loosely; nicknames are fine. |
| Image source | In order: an image attached to the chat, the Mac clipboard, the iMessage thread with that person, a screenshot JC names. |
| Their handle (phone/email) | The iMessage thread where they gave their name. Needed only if the contact has to be created. |
| Which face is theirs | See "Pick the right face" below. |

Never ask JC to re-supply any of these when they are in the conversation, on the clipboard, or in Messages.

## Tools

Load in one ToolSearch call: `+Control_your_Mac osascript`, `+Read_and_Send_iMessages read search`, and `+remote-devices computer` (for `computer_app_screenshot`, `computer_app_click`, `computer_app_ax_find`, `computer_open_application`, `computer_resolve_access`, `computer_request_access`). If the Mac bridge is not connected, wait 15 seconds and retry once, then fall to "Nothing reachable".

Image crops run in Python with Pillow through `scripts/crop_headshot.py`. When running on the Mac itself, `sips` (built in) is the fallback; the script prints the equivalent `sips` command if Pillow is missing.

## Step 1: get the image to a file

Work directory on the Mac: `/tmp/contact-photo/`. Create it with `do shell script "mkdir -p /tmp/contact-photo"`.

**Attached to the chat:** use the attached file's path directly. This is the common case when JC screenshots or pastes into the Claude app.

**Clipboard on the Mac** (JC said "clipboard"): run this AppleScript. It writes PNG data if the clipboard holds an image, or copies the file if it holds a file reference.

```applescript
set outPath to "/tmp/contact-photo/source.png"
try
  set imgData to (the clipboard as «class PNGf»)
  set f to open for access (POSIX file outPath) with write permission
  set eof f to 0
  write imgData to f
  close access f
  return "png"
on error
  try
    set srcFile to (the clipboard as «class furl»)
    do shell script "cp " & quoted form of (POSIX path of srcFile) & " /tmp/contact-photo/source" & "." & (do shell script "echo " & quoted form of (POSIX path of srcFile) & " | sed 's/.*\\.//'")
    return "file"
  on error e
    return "empty: " & e
  end try
end try
```

If it returns "empty", the clipboard has no image. Do not stop: fall through to the iMessage thread.

**iMessage thread:** read the recent messages with that person (`read_imessages`, limit 30). If a message carries an attachment path under `~/Library/Messages/Attachments`, copy that file. If the tool exposes no path, open Messages with computer control, find the photo in the thread, right-click it, choose **Copy**, and run the clipboard script above.

## Step 2: pick the right face

Look at the image (Read it). Then decide who is who:

- JC is usually holding the camera: an Asian man with short black hair, front and center. Exclude him.
- If one other person remains, that's the contact.
- If two or more remain, use what the thread says (a selfie they sent, a description, a name that matches a visible detail). If still tied, pick the most prominent non-JC face, set it, and say in the report who you chose so JC can say "the other one". Do not block on this.

## Step 3: crop to a square headshot

Estimate a box around the head and shoulders as fractions of the frame, then run:

```
python3 scripts/crop_headshot.py <source> /tmp/contact-photo/headshot.jpg --box 0.08 0.02 0.60 0.57
```

The script crops the box, squares it from the top (so the forehead is never cut), resizes to 1024x1024 and writes a JPEG. Read the result. If the chin or hair is clipped, or another person takes more than a corner, widen the box once and rerun. One correction is enough; a slightly loose crop beats a third pass.

On the Mac without Pillow, use the printed `sips` fallback, which the script emits when Pillow is absent.

## Step 4: save it into Contacts

Contacts' AppleScript can only see saved cards. Pick the case that matches:

**A. The contact exists** (`search_contacts` finds it, or JC's card is saved):

```applescript
tell application "Contacts"
  set ps to (every person whose name contains "Durzo")
  if (count of ps) is 0 then error "no contact"
  set p to item 1 of ps
  set image of p to (read (POSIX file "/tmp/contact-photo/headshot.jpg") as JPEG picture)
  save
  return name of p
end tell
```

If several people match, prefer the one whose phone or email equals the iMessage handle.

**B. JC is mid-creation** (he said so, or a screenshot shows an unsaved New Contact card): the card is invisible to AppleScript until saved.

1. `computer_resolve_access` then `computer_request_access` for `com.apple.AddressBook` with reason "Set a contact photo". Skip if already granted this session.
2. `computer_app_screenshot` of Contacts. Confirm the name field holds the person's name. If the card is blank, type the first name (and last name if the thread gave one) into the fields.
3. Click **Done** to save the card. Saving is what JC was about to do anyway; it is not a commitment.
4. Run case A.

**C. No contact and no open card:** create it from the iMessage handle, then set the photo:

```applescript
tell application "Contacts"
  set p to make new person with properties {first name:"Durzo"}
  make new phone at end of phones of p with properties {label:"mobile", value:"+13035551234"}
  set image of p to (read (POSIX file "/tmp/contact-photo/headshot.jpg") as JPEG picture)
  save
end tell
```

Use `make new email` instead when the handle is an email. Say in the report that the card was created.

If the contact already has a photo, save the old one first (`write (image of p) to` a file under `/tmp/contact-photo/previous.tiff`) so it can be put back, then replace it. JC asked for the new one.

## Step 5: verify and report

Take one `computer_app_screenshot` of Contacts showing the card with the new photo, or run `image of p is not missing value` in AppleScript. Then reply in one line, for example:

"Set Durzo's contact photo (red-haired guy, mustache) from the clipboard image. Card was unsaved, so I clicked Done first."

Mention only what JC needs to reverse: which face you picked, whether you created or saved the card, and whether an old photo was replaced.

## Nothing reachable

When no Mac tools load (for example, running in a cloud session), don't make JC debug it:

1. Still do the crop with the script and send the 1024px JPEG with SendUserFile.
2. Tell him in one line: drag it onto the photo circle on the open card and hit Done.
3. Give the one fix for next time: start the request from the Claude desktop app with his Mac selected.

## Guardrails

- Never send an iMessage from this skill. Reading the thread is fine; replying is not the job.
- Never delete a contact or merge cards, even duplicates. Report duplicates instead.
- Never enter passwords or Apple ID credentials.
- Keep other people's faces out of the crop when you can. A group photo becomes one headshot.
