# AWS MCP Research & Documentation Assistant

A powerful Streamlit application that integrates AWS Lab MCP servers with Amazon Nova Pro model for intelligent code analysis, repository research, and documentation generation.

## 🚀 Features

- **Repository Research**: Analyze GitHub repositories using the Git Repo Research MCP server
- **Code Documentation**: Generate comprehensive documentation using the Code Doc Gen MCP server  
- **AI Assistant**: Chat with Amazon Nova Pro for intelligent insights and recommendations
- **AWS Integration**: Seamless integration with AWS Bedrock and Nova Pro model
- **Role-based Access**: Designed for deployment on EC2 with IAM role-based access

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   MCP Servers    │    │  Amazon Nova    │
│   Frontend      │◄──►│                  │    │  Pro (Bedrock)  │
│                 │    │ • Git Repo       │    │                 │
│                 │    │   Research       │    │                 │
│                 │    │ • Code Doc Gen   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- AWS CLI configured or EC2 instance with appropriate IAM roles
- GitHub token (for repository analysis)
- uv/uvx package manager for MCP servers

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aws-mcp-assistant
   ```

2. **Install uv/uvx**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.cargo/env
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   ```bash
   export AWS_REGION=us-west-2
   export AWS_PROFILE=your-profile-name
   export GITHUB_TOKEN=your-github-token
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

### EC2 Deployment

1. **Launch EC2 instance**
   - Use Amazon Linux 2 or Ubuntu
   - Attach IAM role with Bedrock permissions
   - Configure security group to allow port 8501

2. **Deploy using the script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Configure AWS credentials** (if not using IAM roles)
   ```bash
   aws configure
   ```

## 🔐 AWS IAM Permissions

Create an IAM role with the following permissions for EC2 deployment:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
                "arn:aws:bedrock:*::inference-profile/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel",
                "bedrock:ListInferenceProfiles",
                "bedrock:GetInferenceProfile"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🔧 Configuration

### MCP Server Configuration

The application uses two MCP servers:

1. **Git Repo Research Server**
   ```json
   {
     "command": "uvx",
     "args": ["awslabs.git-repo-research-mcp-server@latest"],
     "env": {
       "AWS_PROFILE": "your-profile-name",
       "AWS_REGION": "us-west-2",
       "GITHUB_TOKEN": "your-github-token"
     }
   }
   ```

2. **Code Doc Gen Server**
   ```json
   {
     "command": "uvx", 
     "args": ["awslabs.code-doc-gen-mcp-server@latest"],
     "env": {
       "FASTMCP_LOG_LEVEL": "ERROR"
     }
   }
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `AWS_PROFILE` | AWS profile name | `default` |
| `GITHUB_TOKEN` | GitHub personal access token | Required for repo analysis |
| `STREAMLIT_SERVER_PORT` | Streamlit server port | `8501` |

### Nova Pro Model Configuration

The application uses Amazon Nova Pro with the following parameters:
- **Inference Profile**: `us.amazon.nova-pro-v1:0` (cross-region profile)
- **Max Tokens**: 4000 (configurable)
- **Temperature**: 0.7 (configurable)
- **Content Format**: Text-based messages with proper role structure

**Important**: Nova Pro models require using inference profiles instead of direct model IDs. The application automatically detects and uses the appropriate inference profile.

## 📋 Required Inputs Summary

### Environment Variables (Recommended - set in .env file):
- `AWS_REGION` - Your AWS region (default: us-east-1)
- `AWS_PROFILE` - Your AWS profile (default: default)
- `GITHUB_TOKEN` - Your GitHub personal access token (required for repo analysis)

### UI Inputs (only if not set in environment):
- **Repository Research**: GitHub repository URL + research query
- **Code Documentation**: Code content + documentation type
- **AI Assistant**: Chat prompts (no additional setup needed)

### Optional UI Overrides:
- AWS region and profile (if you want to override environment settings)
- GitHub token (if you want to use a different token)

## 📖 Usage Guide

### 1. Repository Research

**Purpose**: Analyze GitHub repositories for architecture, security, performance, and code quality insights.

**Important**: This feature analyzes the GitHub repository you specify, not your local files or the application's directory.

**Sample Prompts**:
- "Analyze the architecture patterns in this React application"
- "Find potential security vulnerabilities in the authentication system"
- "Identify performance bottlenecks in the database queries"
- "Review code quality metrics and suggest improvements"
- "Map dependencies and identify outdated packages"

**Steps**:
1. Navigate to the "Repository Research" tab
2. Configure your GitHub token in the sidebar (required)
3. Enter the GitHub repository URL (must start with https://github.com/)
4. Provide a specific research query
5. Click "Analyze Repository"
6. Review MCP server results and AI-enhanced insights

**Requirements**:
- Valid GitHub personal access token
- Public GitHub repository URL or private repo with token access
- Internet connection for GitHub API access

### 2. Code Documentation

**Purpose**: Generate comprehensive documentation for code snippets, functions, classes, or entire modules.

**Sample Prompts**:
- Generate API documentation for REST endpoints
- Create README documentation for a Python package
- Document inline comments for complex algorithms
- Generate tutorial documentation with examples

**Steps**:
1. Navigate to the "Code Documentation" tab
2. Paste your code in the text area
3. Select documentation type (API, README, inline, tutorial)
4. Click "Generate Documentation"
5. Review generated docs and AI enhancements

### 3. AI Assistant

**Purpose**: Interactive chat with Amazon Nova Pro for code analysis, best practices, and technical guidance.

**Sample Prompts**:
- "How can I improve the security of my Python Flask application?"
- "What are the best practices for API documentation in microservices?"
- "Explain the repository analysis results in simple terms"
- "How do I optimize this database query for better performance?"
- "What testing strategies should I implement for this React component?"
- "Review this code for potential memory leaks"
- "Suggest improvements for this API design"

## 🎯 Sample Use Cases

### Use Case 1: Security Audit
```
Repository: https://github.com/your-org/web-app
Query: "Perform a comprehensive security audit focusing on authentication, authorization, and data validation"

Expected Output:
- Security vulnerability assessment
- Authentication flow analysis
- Data validation recommendations
- Security best practices suggestions
```

### Use Case 2: Performance Optimization
```
Repository: https://github.com/your-org/api-service
Query: "Analyze performance bottlenecks and suggest optimization strategies"

Expected Output:
- Database query optimization suggestions
- Caching strategy recommendations
- Code efficiency improvements
- Resource utilization analysis
```

### Use Case 3: Documentation Generation
```
Code: Python Flask API endpoints
Documentation Type: API

Expected Output:
- OpenAPI/Swagger documentation
- Endpoint descriptions and parameters
- Request/response examples
- Error handling documentation
```

## 🔍 Advanced Features

### Custom Analysis Queries

The application supports sophisticated analysis queries:

- **Architecture Analysis**: "Map the microservices architecture and identify coupling issues"
- **Code Quality**: "Assess code maintainability using SOLID principles"
- **Security Review**: "Identify OWASP Top 10 vulnerabilities in the codebase"
- **Performance Audit**: "Analyze algorithmic complexity and suggest optimizations"

### Multi-language Support

The MCP servers and Nova Pro model support analysis of:
- Python, JavaScript/TypeScript, Java, C#, Go, Rust
- Web frameworks (React, Angular, Vue, Django, Flask, Express)
- Cloud-native applications (Docker, Kubernetes, Terraform)

## 🚨 Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   ```bash
   # Check if uvx is installed
   uvx --version
   
   # Reinstall if needed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **AWS Credentials Error**
   ```bash
   # Check AWS configuration
   aws sts get-caller-identity
   
   # Configure if needed
   aws configure
   ```

3. **Bedrock Access Denied**
   - Verify IAM permissions for Bedrock
   - Ensure Nova Pro model is available in your region
   - Check if model access is enabled in Bedrock console

4. **Nova Pro Inference Profile Issues**
   ```bash
   # List available inference profiles
   aws bedrock list-inference-profiles --region us-east-1
   
   # Test Nova Pro with inference profile
   aws bedrock-runtime invoke-model \
     --model-id us.amazon.nova-pro-v1:0 \
     --body '{"messages":[{"role":"user","content":[{"text":"Hello"}]}],"inferenceConfig":{"max_new_tokens":100,"temperature":0.7}}' \
     --cli-binary-format raw-in-base64-out \
     --region us-east-1 \
     output.json
   ```
   - **Critical**: Use inference profile ID (e.g., `us.amazon.nova-pro-v1:0`) not direct model ID
   - Ensure you're using the correct message format with content arrays
   - Use `max_new_tokens` instead of `max_tokens`
   - Don't use unsupported parameters like `top_p`

5. **Access Denied Errors**
   ```bash
   # Check if you have model access
   aws bedrock list-foundation-models --region us-east-1 | grep nova
   
   # Check inference profiles
   aws bedrock list-inference-profiles --region us-east-1
   
   # Verify your identity
   aws sts get-caller-identity
   ```
   - Ensure Nova Pro model access is enabled in Bedrock console
   - Verify your IAM role/user has the correct permissions
   - Check if you're using the correct AWS region
   - Request model access in Bedrock console if needed

6. **Inference Profile Not Found**
   - Check if Nova Pro is available in your region
   - Verify model access is enabled in Bedrock console
   - Try using cross-region inference profile: `us.amazon.nova-pro-v1:0`

4. **GitHub Token Issues**
   - Verify token has repo access permissions
   - Check token expiration
   - Ensure token is properly set in environment

### Logs and Debugging

```bash
# Check application logs
sudo journalctl -u aws-mcp-assistant -f

# Check MCP server logs
export FASTMCP_LOG_LEVEL=DEBUG

# Test Bedrock connectivity
aws bedrock list-foundation-models --region us-west-2
```

## 🔄 Updates and Maintenance

### Updating MCP Servers
```bash
# MCP servers auto-update when using uvx
# Force update if needed
uvx --force awslabs.git-repo-research-mcp-server@latest
uvx --force awslabs.code-doc-gen-mcp-server@latest
```

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart aws-mcp-assistant
```

## 📊 Monitoring and Analytics

### Health Checks
- Application health: `http://your-ec2-ip:8501/_stcore/health`
- Service status: `sudo systemctl status aws-mcp-assistant`

### Performance Monitoring
- Monitor Bedrock API usage in CloudWatch
- Track MCP server response times
- Monitor EC2 instance resources

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review AWS Bedrock documentation
- Check MCP server documentation
- Open an issue in the repository

## 🔗 Useful Links

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon Nova Pro Model Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [uv Package Manager](https://docs.astral.sh/uv/)