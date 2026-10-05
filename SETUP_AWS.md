# AWS setup

About 30–40 minutes. Do the steps in order. Every step is free. Nothing here starts an hourly charge.

Use **US East (N. Virginia) / us-east-1** for everything. Check the region picker at the top right of the console.

---

## 1. Secure the root account
1. Sign in to the AWS console as root (the email you signed up with).
2. Top-right account menu → **Security credentials** → **Assign MFA device**. Use an authenticator app.

## 2. Budget alert ($10)
1. Search **Budgets** → **Create budget** → **Use a template** → **Monthly cost budget**.
2. Name it `pv-eval-budget`. Amount: **10** USD. Email: yours.
3. Create it. AWS emails you at 85% and 100% of actual spend, and when the forecast passes 100%.

This is an alert, not a hard cap. You'll be told about spending, but AWS won't stop it on its own.

## 3. Anthropic first-time-use form (needed once for Claude models)
1. Search **Amazon Bedrock** and confirm the region is **us-east-1**.
2. Left menu → **Model catalog** → open the Claude model you plan to run (**Claude Haiku 4.5** here).
3. If you're prompted to **submit use case details**, fill in the form yourself. An honest description works, e.g.: *"Personal, non-commercial evaluation of a customer-support prototype grounded in public help-center articles. Low volume (a few hundred requests)."*
4. Submit. Approval is usually quick, but it can take a while on new accounts.

You don't need to request access for Llama or Nova. Bedrock subscribes to third-party models automatically the first time they're called. That's why the policy in step 4 includes three AWS Marketplace permissions. The first call can take up to about 15 minutes to settle.

## 4. Create a limited IAM user for the scripts
The scripts never use root. This user can only call the models named in the policy below.

1. Search **IAM** → **Users** → **Create user**. Name: `pv-eval`. Do **not** give it console access. → Next.
2. **Attach policies directly** → don't select any → Next → **Create user**.
3. Open `pv-eval` → **Add permissions** → **Create inline policy** → **JSON** tab. Paste the policy below. Name it `pv-eval-bedrock` and create it.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "UsInferenceProfiles",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": [
        "arn:aws:bedrock:us-east-1:*:inference-profile/us.anthropic.claude-sonnet-5-5",
        "arn:aws:bedrock:us-east-1:*:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:us-east-1:*:inference-profile/us.meta.llama4-maverick-17b-instruct-v1:0",
        "arn:aws:bedrock:us-east-1:*:inference-profile/us.amazon.nova-2-lite-v1:0"
      ]
    },
    {
      "Sid": "ModelsBehindTheProfiles",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-5-5",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:*::foundation-model/meta.llama4-maverick-17b-instruct-v1:0",
        "arn:aws:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0"
      ],
      "Condition": {
        "StringLike": {
          "bedrock:InferenceProfileArn": "arn:aws:bedrock:us-east-1:*:inference-profile/us.*"
        }
      }
    },
    {
      "Sid": "TitanEmbeddingsInRegion",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
    },
    {
      "Sid": "AutoSubscribeThirdPartyModels",
      "Effect": "Allow",
      "Action": [
        "aws-marketplace:Subscribe",
        "aws-marketplace:Unsubscribe",
        "aws-marketplace:ViewSubscriptions"
      ],
      "Resource": "*"
    }
  ]
}
```

4. Still on `pv-eval` → **Security credentials** tab → **Create access key** → choose **Command Line Interface (CLI)** → tick the confirmation → Create.
5. Keep that page open for step 5. **Don't paste the keys into a chat, an email, or any file in the project folder.**

## 5. Put the key on your Mac (in Terminal)
1. Install the AWS CLI v2 from AWS's official macOS installer: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
2. Run:
   ```
   aws configure --profile pv-eval
   ```
   Paste the access key ID and secret when asked. Region: `us-east-1`. Output format: `json`.
3. Check that it worked. This is free and only confirms who you are:
   ```
   aws sts get-caller-identity --profile pv-eval
   ```
   You should see an ARN ending in `user/pv-eval`.

The key is stored in `~/.aws/credentials` on your Mac, outside the project folder. When the project is finished, delete the access key in IAM (`pv-eval` → Security credentials → Deactivate → Delete).

## 6. Python environment (in Terminal, inside the project folder)
```
cd "<path to>/prime-video-support-eval"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 7. First commands
These are free (no Bedrock calls):
```
python src/extract_articles.py <folder-with-saved-pages> data
python src/build_index.py          # prints the cost estimate only
```
The first paid step is `python src/build_index.py --yes`, which costs under $0.01. Every paid script prints an estimate first and does nothing until you add `--yes`.
