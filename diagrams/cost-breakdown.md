# AWS Cost Breakdown (Lambda Architecture)

## Core Services

### 1. **API Gateway**
- Pay-per-request
- ~ $1.00 per million requests
- Estimated: **$1–3/month**

### 2. **AWS Lambda**
- 1M free requests/month
- After that: ~$0.20 per million
- Typical usage will stay almost free
- Estimated: **$0–2/month**

### 3. **DynamoDB**
- On-Demand mode for simplicity
- Light read/write traffic: **$1–5/month**
- Storage: pennies

### 4. **S3**
- Store attachments / logs
- **$0.50–1/month**

### 5. **SES or SNS**
- Email (SES): $0.10 per 1,000 emails
- SMS via SNS: varies by region (e.g. ~$0.014/SMS)

### 6. **EventBridge**
- $1.00 per million events
- Estimated: **<$1/month**

---

## Total Estimated Monthly Cost
| Usage | Estimated Cost |
|-------|----------------|
| Low (MVP) | **$3–8/month** |
| Medium | **$10–25/month** |
| High | **$50–120/month** |

Lambda architecture keeps costs extremely low until I need to scale.


