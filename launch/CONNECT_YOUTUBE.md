# Connect your YouTube channel (one time, about 10 minutes)

This lets me upload and schedule videos and read their stats. Your password is never shared:
you approve access on Google's own pages and save three values in your environment settings.
Don't paste them into the chat.

Doing this on a phone works best with your browser set to **"Desktop site"**.

## 1. Create a Google Cloud project
1. Open **console.cloud.google.com** and sign in with the Google account that owns the channel.
2. Top bar > project picker > **New project** > name it `Last Light Uploader` > Create.

## 2. Turn on the YouTube APIs
3. Menu > **APIs & Services > Library**. Search **YouTube Data API v3** > **Enable**.
4. Do the same for **YouTube Analytics API**.

## 3. Consent screen
5. Menu > **Google Auth Platform** (or "OAuth consent screen") > **Get started**.
   App name `Last Light Uploader`, your email, Audience **External**, then finish.
6. **Audience** > **Publish app** > Confirm. *(If you skip this, the connection expires after 7 days.
   You'll see an "unverified app" warning later. That's normal for your own private app.)*

## 4. Create the key
7. **Clients** (or Credentials) > **Create client** > type **Web application**.
8. Under **Authorized redirect URIs** add: `https://developers.google.com/oauthplayground`
9. Create. Keep the **Client ID** and **Client secret** open.

## 5. Approve access and get the refresh token
10. Open **developers.google.com/oauthplayground**.
11. Tap the **gear icon** (top right) > tick **Use your own OAuth credentials** > paste the Client ID and secret.
12. In the box **"Input your own scopes"** paste exactly:
    `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl https://www.googleapis.com/auth/yt-analytics.readonly`
13. **Authorize APIs** > pick the account > if asked, pick the **Last Light Stories** channel >
    **Advanced > Go to Last Light Uploader** > Allow.
14. **Exchange authorization code for tokens** > copy the **Refresh token**.

## 6. Save the three values (not in chat)
15. In the Claude app, open this session's **cloud environment menu** (title bar) > **YouTube** environment > **Edit**,
    and add these **environment variables**:
    - `YT_CLIENT_ID` = the Client ID
    - `YT_CLIENT_SECRET` = the Client secret
    - `YT_REFRESH_TOKEN` = the refresh token
16. Tell me "connected". I'll run a check that prints your channel name, then take over uploads.

Note: YouTube has kept videos uploaded by new, unaudited apps **private**. If that still applies, the check
upload will show it, and I'll prepare the free audit form for you. Until it's approved, keep posting from the YouTube app
(I'll keep sending ready-to-post files). Stats and analytics still work either way.
