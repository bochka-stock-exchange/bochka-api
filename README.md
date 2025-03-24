# 📈 bochka-api - Educational Stock Market Simulation

[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![Dockerized](https://img.shields.io/badge/Docker-Supported-blue)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Educational Project](https://img.shields.io/badge/Status-Educational-orange)](https://github.com/your-repo)
![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/bochka-stock-exchange/bochka-api?utm_source=oss&utm_medium=github&utm_campaign=bochka-stock-exchange%2Fbochka-api&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

## 🎯 About the Project
🚀 **bochka-api** is a stock market simulation API built for educational purposes. It allows users to trade financial instruments in a sandboxed environment. This project is **not intended for real-world financial applications** and should not be used for actual trading.

The system models key aspects of a stock exchange:
- 📊 Order execution mechanisms
- 💰 Balance management for users
- 💹 Exchange commission handling
- ⏳ Trading session control

The API follows the OpenAPI specification and can be integrated into frontend applications.

## ✨ Features
- 🔐 **User authentication and registration**
- 📈 **Trading operations** (market and limit orders, order book management)
- 💵 **Balance management** (currencies and custom assets)
- ⚙️ **Administrative control panel** (managing instruments, user balances, and exchange settings)
- 📜 **Optional features** (trade history, candlestick data output)

## 🚀 Installation & Deployment

### 📌 Prerequisites
To run the project, ensure you have:
- 🐳 [Docker](https://www.docker.com/)
- 🛠️ [Make](https://www.gnu.org/software/make/)

### ▶️ Running in Development Mode
```sh
make up
```
Starts the application in a Docker container.

### ⏹️ Stopping the Development Environment
```sh
make down
```

### 🔥 Running in Production Mode
```sh
make up-prod
```
Starts the production-ready version of the application.

### ❌ Stopping the Production Environment
```sh
make down-prod
```

### 📂 Running Migrations
```sh
make migrate
```
Applies database migrations.

### 📦 Installing Dependencies
```sh
make install-deps
```

### 🔍 Running Linter & Formatting Code
```sh
make lint
make format
```

### 🧪 Running Tests
```sh
make test
```

### 🚀 Starting the Application
```sh
make start
```

## 📚 API Documentation
The API is documented using OpenAPI and can be explored via [Swagger Editor](https://editor-next.swagger.io) using the provided `openapi.json` file.

## ⚠️ Disclaimer
**This is an educational project and is not suitable for real-world financial transactions.** It is intended for learning and demonstration purposes only.

## 📜 License
This project is licensed under the MIT License.
