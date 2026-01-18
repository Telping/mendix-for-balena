# Deployment Guide

## Recommended: Raspberry Pi with Balena.io

This is the **recommended deployment method** for a personal dog diary project because:

1. ✅ **One-time cost** - No monthly cloud bills
2. ✅ **Simple management** - Balena handles everything
3. ✅ **Automatic updates** - Push code and all devices update
4. ✅ **Local storage** - All precious memories stored at home
5. ✅ **Remote access** - Access from anywhere with public URL or Cloudflare tunnel

### Complete Balena Setup (15 minutes)

#### Step 1: Install Balena CLI (2 min)

```bash
npm install -g balena-cli
balena login
```

#### Step 2: Create Application (1 min)

```bash
balena app create boxty-diary --type raspberrypi4-64
```

#### Step 3: Prepare Raspberry Pi (5 min)

1. Visit https://dashboard.balena-cloud.com
2. Click your app → "Add device"
3. Download BalenaOS image
4. Flash to SD card with [Balena Etcher](https://www.balena.io/etcher/)
5. Insert SD into Pi and power on
6. Wait for device to appear in dashboard (~2-5 minutes)

#### Step 4: Deploy Application (5 min)

```bash
cd boxty-diary
balena push boxty-diary
```

Balena will build and deploy automatically. First build takes ~10 minutes.

#### Step 5: Configure Environment Variables (2 min)

In Balena dashboard:
1. Go to your application
2. Click "Environment Variables"
3. Add:
   - Name: `SECRET_KEY`, Value: `<generate-random-string>`
   - Name: `FLASK_ENV`, Value: `production`

#### Step 6: Access Your Diary

**Option A - Local Network**:
- Find IP in dashboard, visit `http://<ip-address>`

**Option B - Public URL** (recommended):
- Enable "Public Device URL" in device settings
- Use provided URL anywhere

**Option C - Custom Domain**:
- Set up Cloudflare Tunnel (see below)

### Cloudflare Tunnel Setup (Optional)

For custom domain without exposing home IP:

1. Install Cloudflare Tunnel on your Pi
2. Add to `docker-compose.balena.yml`:

```yaml
  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    restart: always
```

3. Set `CLOUDFLARE_TUNNEL_TOKEN` in Balena environment variables
4. Access via your domain (e.g., `boxty.yourdomain.com`)

### Balena Fleet Management

```bash
# View logs
balena logs <device-uuid> --tail

# SSH into device
balena ssh <device-uuid>

# Restart app
balena restart <device-uuid>

# Update app (just push!)
git commit -am "updates"
balena push boxty-diary
```

### Storage Management

Uploads and database are stored in persistent volumes:
- `uploads-data`: All photos/videos
- `db-data`: SQLite database

**To backup**:
```bash
balena ssh <device-uuid>
# Inside container
tar -czf /tmp/backup.tar.gz /app/app/static/uploads
# Copy out using balena CLI
```

**External USB Storage** (for more space):

1. Format USB drive as ext4
2. Add to `docker-compose.balena.yml`:

```yaml
volumes:
  uploads-data:
    driver: local
    driver_opts:
      type: none
      device: /mnt/usb-storage
      o: bind
```

## Alternative: AWS ECS Deployment

### When to use AWS:
- Need to share with many users
- Want automatic scaling
- Need high availability
- Don't have Raspberry Pi

### Quick AWS Setup

1. **Install AWS CLI**:
```bash
pip install awscli
aws configure
```

2. **Run setup script**:
```bash
chmod +x aws-setup.sh
./aws-setup.sh
```

3. **Configure GitHub Secrets**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

4. **Push to GitHub main branch** - Automatic deployment!

### Manual AWS Setup

See [README.md](README.md) for detailed AWS instructions.

### AWS Costs Estimate

- **ECS Fargate**: ~$15-30/month for small instance
- **RDS PostgreSQL**: ~$15-25/month for db.t3.micro
- **EFS Storage**: ~$0.30/GB/month
- **Data transfer**: ~$0.09/GB

**Total**: ~$40-60/month minimum

## Comparison: Balena vs AWS

| Feature | Balena (Raspberry Pi) | AWS |
|---------|----------------------|-----|
| Setup Time | 15 minutes | 1-2 hours |
| Monthly Cost | $0 (after Pi purchase) | $40-60+ |
| Scalability | Single device | Auto-scaling |
| Management | Very simple | Complex |
| Storage Cost | One-time (SD/USB) | Pay per GB |
| Updates | One command | CI/CD pipeline |
| Best For | Personal use | Production apps |

## Production Checklist

- [ ] Change `SECRET_KEY` to secure random string
- [ ] Enable HTTPS (Cloudflare or Let's Encrypt)
- [ ] Set up automated backups
- [ ] Configure external storage (if using Pi)
- [ ] Test file uploads (images/videos)
- [ ] Test geolocation on mobile
- [ ] Set up monitoring/alerts
- [ ] Document your custom domain setup
- [ ] Test disaster recovery process

## Monitoring

### Balena
- Built-in dashboard shows device status
- View logs in real-time
- CPU/Memory metrics available
- Email alerts for device offline

### AWS
- CloudWatch for logs and metrics
- Set up alarms for errors
- Use AWS X-Ray for tracing
- Configure SNS for alerts

## Updating the Application

### Balena
```bash
git pull origin main
balena push boxty-diary
```
All devices update automatically!

### AWS
```bash
git push origin main
```
GitHub Actions deploys automatically!

## Backup Strategies

### Raspberry Pi
1. **Daily automated backups** using cron
2. **Weekly manual verification**
3. **External backup** to NAS or cloud
4. **SD card image** monthly

### AWS
1. **Automated RDS snapshots** (daily)
2. **S3 versioning** enabled
3. **AWS Backup** service configured
4. **Cross-region replication** (optional)

## Troubleshooting

### Balena: Device Offline
1. Check power supply
2. Check network connection
3. View device diagnostics in dashboard
4. Reboot via dashboard

### Balena: Build Fails
```bash
# Check logs
balena logs <device-uuid>

# Rebuild without cache
balena push boxty-diary --nocache
```

### AWS: Deployment Fails
1. Check GitHub Actions logs
2. Verify AWS credentials
3. Check ECS task logs in CloudWatch
4. Verify security groups allow port 5000

### Out of Storage
**Raspberry Pi**:
- Check storage: `df -h`
- Add external USB drive
- Clean old uploads

**AWS**:
- Increase EFS size
- Implement S3 lifecycle policies
- Compress old videos

## Getting Help

- **Balena Forums**: https://forums.balena.io/
- **Balena Docs**: https://www.balena.io/docs/
- **AWS Support**: https://console.aws.amazon.com/support/
- **GitHub Issues**: Create an issue in this repo

---

**Recommendation**: Start with Balena for simplicity and cost savings. You can always migrate to AWS later if needed!
