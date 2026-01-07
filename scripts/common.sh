#!/bin/bash
# Common functions for deploy scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$SCRIPT_DIR/infra"

# Load .env and set up Terraform variables
load_env() {
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        error "Missing .env file - copy from .env.example and fill in values"
    fi

    set -a
    source "$SCRIPT_DIR/.env"
    set +a

    if [ -z "$PERCEPTRON_API_KEY" ]; then
        error "PERCEPTRON_API_KEY not set in .env"
    fi

    # Prompt for region if not provided
    if [ -z "$AWS_REGION" ]; then
        read -p "AWS region [us-west-2]: " AWS_REGION
        AWS_REGION="${AWS_REGION:-us-west-2}"
    fi

    export TF_VAR_aws_region="$AWS_REGION"
    export TF_VAR_perceptron_api_key="$PERCEPTRON_API_KEY"
    export TF_VAR_domain_name="$DOMAIN_NAME"
    export AWS_REGION

    log "Using AWS region: $AWS_REGION"
}

# Ensure AWS credentials are valid, prompting for SSO login if needed
aws_login() {
    if aws sts get-caller-identity &>/dev/null; then
        log "AWS credentials valid"
        return 0
    fi

    if [ -z "$AWS_PROFILE" ]; then
        PROFILES=$(grep '^\[profile ' ~/.aws/config 2>/dev/null | sed 's/\[profile \(.*\)\]/\1/' | tr '\n' ' ')
        if [ -n "$PROFILES" ]; then
            echo "Available profiles: $PROFILES"
            read -p "AWS profile name: " AWS_PROFILE
            export AWS_PROFILE
        fi
    fi

    if [ -n "$AWS_PROFILE" ]; then
        log "Logging in with profile: $AWS_PROFILE"
        aws sso login --profile "$AWS_PROFILE"
    else
        warn "No AWS profile configured. Setting up SSO..."
        aws configure sso
        read -p "Enter the profile name you just created: " AWS_PROFILE
        export AWS_PROFILE
    fi

    if ! aws sts get-caller-identity &>/dev/null; then
        error "AWS login failed. Try: export AWS_PROFILE=your-profile-name"
    fi
    log "AWS login successful (profile: $AWS_PROFILE)"
}
