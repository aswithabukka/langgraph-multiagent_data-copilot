# 🚀 Deployment Guide - LangGraph Multi-Agent Data Analysis Copilot

## 📋 **Quick Start**

### **Prerequisites**
- Python 3.11+
- OpenAI API Key
- Git

### **1. Clone & Setup**
```bash
git clone https://github.com/aswithabukka/langgraph-multiagent_data-copilot.git
cd langgraph-multiagent_data-copilot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Configuration**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### **3. Initialize Database**
```bash
python scripts/init_db.py
```

### **4. Start Services**
```bash
# Option 1: Start both services automatically
python start_services.py

# Option 2: Start manually
# Terminal 1 - API Server
python main.py

# Terminal 2 - Streamlit UI  
streamlit run ui/streamlit_app.py
```

### **5. Access Applications**
- **Streamlit UI**: http://localhost:8501
- **API Server**: http://localhost:8008
- **API Docs**: http://localhost:8008/docs

---

## 🐳 **Docker Deployment**

### **Using Docker Compose (Recommended)**
```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### **Manual Docker Build**
```bash
# Build API container
docker build -t langgraph-api .

# Build Streamlit container  
docker build -f Dockerfile.streamlit -t langgraph-ui .

# Run containers
docker run -p 8008:8008 --env-file .env langgraph-api
docker run -p 8501:8501 langgraph-ui
```

---

## 🧪 **Testing & Validation**

### **Run Test Suite**
```bash
# Comprehensive system test
python test_comprehensive.py

# Full system integration test
python test_full_system.py

# Database schema test
python test_new_schema.py

# Individual component tests
python -m pytest tests/
```

### **API Health Check**
```bash
curl http://localhost:8008/api/health
```

### **Sample Test Queries**
```bash
# Arithmetic (instant response)
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "What is 25*4+10?"}' \
  http://localhost:8008/api/infer

# Business Analytics  
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "Show me profit margins by product category with a chart"}' \
  http://localhost:8008/api/infer
```

---

## 📊 **Database Schema**

The system includes a comprehensive 7-table business database:

| Table | Records | Purpose |
|-------|---------|---------|
| **regions** | 4 | Geographic sales territories |
| **categories** | 4 | Product categories with margins |
| **sales_reps** | 6 | Sales team performance data |
| **customers** | 8 | Customer companies & details |
| **products** | 22 | Product catalog with pricing |
| **orders** | 27 | Order lifecycle tracking |
| **order_items** | 35+ | Detailed line items with discounts |

---

## 🎯 **Query Examples**

### **Instant Arithmetic**
- `"What is 15 * 8 + 25?"`
- `"Calculate (100 + 50) / 3"`

### **Business Analytics**
- `"Show me total revenue by sales representative"`
- `"What are the top 5 customers by purchase amount?"`
- `"Display profit margins by product category with a bar chart"`
- `"Which region has the highest sales performance?"`

### **Complex Analysis**
- `"Compare Q2 vs Q3 2024 sales performance"`
- `"Show customer acquisition trends by region"`
- `"Calculate commission earnings for each sales rep"`
- `"Display inventory levels with reorder recommendations"`

---

## 🔧 **Configuration Options**

### **Environment Variables**
```bash
# API Configuration
API_HOST=localhost
API_PORT=8008
API_DEBUG=false

# Database
DATABASE_URL=sqlite:///./data.db

# LLM Configuration  
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=optional_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Chart Configuration
CHART_DIR=./charts

# Logging
LOG_LEVEL=INFO
```

### **Agent Configuration**
Edit `app/agents/config.py` to customize:
- LLM providers and models
- Temperature settings
- Agent-specific configurations

---

## 📈 **Production Deployment**

### **Recommended Setup**
1. **Load Balancer**: nginx or similar
2. **Process Manager**: gunicorn for API, supervisor for services
3. **Database**: PostgreSQL for production (SQLite for development)
4. **Monitoring**: Health check endpoints included
5. **Scaling**: Horizontal scaling supported

### **Security Considerations**
- Store API keys in secure environment variables
- Use HTTPS in production
- Implement rate limiting
- Regular security updates

### **Performance Optimization**
- Enable caching for frequent queries
- Database indexing for large datasets
- Chart generation optimization
- API response compression

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Kill existing processes
pkill -f "python main.py"
pkill -f "streamlit run"

# Or use different ports
API_PORT=8009 python main.py
```

#### **Database Issues**
```bash
# Reinitialize database
rm -f data.db
python scripts/init_db.py
```

#### **Chart Generation Issues**
```bash
# Check charts directory
ls -la charts/

# Verify matplotlib backend
python -c "import matplotlib; print(matplotlib.get_backend())"
```

#### **API Connection Issues**
```bash
# Test API connectivity
curl http://localhost:8008/api/health

# Check logs
tail -f logs/app.log
```

---

## 📚 **Documentation**

- **API Documentation**: http://localhost:8008/docs (when running)
- **Database Schema**: `DATABASE_SCHEMA.md`
- **Sample Queries**: `SAMPLE_QUERIES.md`
- **Enhanced Features**: `ENHANCED_FEATURES.md`
- **Main README**: `README.md`

---

## 🤝 **Support**

For issues, questions, or contributions:
1. Check existing documentation
2. Review troubleshooting guide
3. Create GitHub issue with detailed description
4. Include logs and error messages

---

## 🎉 **Success Indicators**

✅ **System is working correctly when:**
- API health check returns 200 OK
- Streamlit UI loads without errors
- Database schema shows 7 tables
- Sample queries return results
- Charts generate and display properly
- All test suites pass

**🚀 Ready for production use!**
