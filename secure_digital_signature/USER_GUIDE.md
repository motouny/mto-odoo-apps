# User Guide

## Creating and sending a request

1. **Digital Signature -> My Signature Requests -> New**.
2. Fill in the subject, description and signing mode (Sequential or
   Parallel), then upload the **Original PDF** under "Original Document".
3. Under the **Signers** tab, add each signer (Internal User, Portal
   Contact, or External with just a name + email) in the order they
   should sign for sequential mode.
4. For each signer, click **Fields** to place their Signature/Initials/
   Name/Date/Text/Checkbox/Selection/Stamp fields: pick the page number
   and enter the X/Y position and width/height as percentages of the
   page (0-100, measured from the top-left corner).
5. Click **Mark Ready**, review, then **Send**. In Sequential mode only
   the first signer is notified; in Parallel mode everyone is notified
   at once.

## What a signer sees

Each signer receives an email with a personal, single-use link
(`/sign/<token>`). They can view the original document, fill in their
fields (draw a signature with the mouse/touch or type into text/date/
selection/checkbox fields), then **Sign Document** - or **Reject
Document** with an optional reason. A signature-pad canvas is used for
Signature/Initials/Stamp fields; nothing is uploaded until they submit.

## What happens on completion

Once every required signer has signed, the app automatically:

- Burns every field into the actual PDF pages and stores the result as
  the **Final Signed** document.
- Computes the SHA-256 hash of the final document.
- Generates a **Completion Certificate** PDF listing every signer, their
  signing timestamp and IP address, both document hashes, and a QR code
  linking to the public verification page.
- Emails every signer with a link to verify the document online.

## Verifying a document

Anyone with the QR code or verification link
(`/sign/verify/<verification_token>`) can confirm a document is valid
and see its completion date - without ever seeing any signer's name,
email or IP address. Every verification attempt is itself logged.

## Reminders and expiration

- A daily cron reminds any signer who hasn't yet signed, every
  **Reminder Interval Days** (default 3).
- An hourly cron automatically expires requests past their **Expiration
  Date**, revoking any signer tokens that haven't been used yet.

## Roles

| Group | Can do |
|---|---|
| User | Create/send/resend/cancel their own requests |
| Manager | Everything a User can, for every request in the company; manage Templates |
