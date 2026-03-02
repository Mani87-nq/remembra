#!/usr/bin/env bash
# Remembra Cloud — Fly.io deployment helper
#
# Prerequisites:
#   brew install flyctl
#   fly auth login
#
# First-time setup:
#   fly apps create remembra-cloud
#   fly volumes create remembra_data --region iad --size 10
#   ./scripts/fly-deploy.sh secrets
#   ./scripts/fly-deploy.sh deploy
#
# Subsequent deploys:
#   ./scripts/fly-deploy.sh deploy

set -euo pipefail

APP_NAME="remembra-cloud"

case "${1:-deploy}" in
  secrets)
    echo "Setting Fly.io secrets for $APP_NAME..."
    echo "You'll be prompted for each secret value."
    echo ""

    read -rp "REMEMBRA_AUTH_MASTER_KEY: " MASTER_KEY
    read -rp "REMEMBRA_OPENAI_API_KEY: " OPENAI_KEY
    read -rp "REMEMBRA_QDRANT_URL: " QDRANT_URL
    read -rp "REMEMBRA_QDRANT_API_KEY: " QDRANT_KEY
    read -rp "REMEMBRA_STRIPE_SECRET_KEY: " STRIPE_KEY
    read -rp "REMEMBRA_STRIPE_WEBHOOK_SECRET: " STRIPE_WEBHOOK

    fly secrets set \
      REMEMBRA_AUTH_MASTER_KEY="$MASTER_KEY" \
      REMEMBRA_OPENAI_API_KEY="$OPENAI_KEY" \
      REMEMBRA_QDRANT_URL="$QDRANT_URL" \
      REMEMBRA_QDRANT_API_KEY="$QDRANT_KEY" \
      REMEMBRA_STRIPE_SECRET_KEY="$STRIPE_KEY" \
      REMEMBRA_STRIPE_WEBHOOK_SECRET="$STRIPE_WEBHOOK" \
      --app "$APP_NAME"

    echo ""
    echo "✅ Secrets set. Run './scripts/fly-deploy.sh deploy' to deploy."
    ;;

  deploy)
    echo "Deploying $APP_NAME to Fly.io..."
    fly deploy --app "$APP_NAME"
    echo ""
    echo "✅ Deployed! Check status: fly status --app $APP_NAME"
    echo "   Logs: fly logs --app $APP_NAME"
    echo "   URL:  https://$APP_NAME.fly.dev"
    ;;

  status)
    fly status --app "$APP_NAME"
    ;;

  logs)
    fly logs --app "$APP_NAME"
    ;;

  ssh)
    fly ssh console --app "$APP_NAME"
    ;;

  *)
    echo "Usage: $0 {secrets|deploy|status|logs|ssh}"
    exit 1
    ;;
esac
