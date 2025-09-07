#!/bin/bash

# AWS MCP Research & Documentation Assistant Deployment Script
# This script deploys the Streamlit application on an EC2 instance

set -e

echo "🚀 Starting deployment of AWS MCP Research & Documentation Assistant..."

# Update system packages
echo "📦 Updating system packages..."
sudo yum update -y

# Install Python 3.9+ if not already installed
echo "🐍 Installing Python..."
sudo yum install -y python3 python3-pip

# Install uv and uvx for MCP server management
echo "⚡ Installing uv and uvx..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Create application directory
APP_DIR="/opt/aws-mcp-assistant"
echo "📁 Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown ec2-user:ec2-user $APP_DIR

# Copy application files
echo "📋 Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
echo "🔐 Setting up environment variables..."
cat > .env << EOF
AWS_REGION=us-west-2
AWS_PROFILE=default
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF

# Create systemd service file
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/aws-mcp-assistant.service > /dev/null << EOF
[Unit]
Description=AWS MCP Research & Documentation Assistant
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/home/ec2-user/.cargo/bin
ExecStart=$APP_DIR/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "🔄 Enabling and starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable aws-mcp-assistant
sudo systemctl start aws-mcp-assistant

# Configure firewall (if firewalld is running)
if sudo systemctl is-active --quiet firewalld; then
    echo "🔥 Configuring firewall..."
    sudo firewall-cmd --permanent --add-port=8501/tcp
    sudo firewall-cmd --reload
fi

# Check service status
echo "✅ Checking service status..."
sudo systemctl status aws-mcp-assistant --no-pager

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your AWS credentials using 'aws configure' or IAM roles"
echo "2. Set your GitHub token in the environment or through the web interface"
echo "3. Access the application at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo ""
echo "🔧 Useful commands:"
echo "- Check logs: sudo journalctl -u aws-mcp-assistant -f"
echo "- Restart service: sudo systemctl restart aws-mcp-assistant"
echo "- Stop service: sudo systemctl stop aws-mcp-assistant"