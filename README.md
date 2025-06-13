# Advance Loan Calc

## Overview

**Advance Loan Calc** is a Python-based application designed to help organizations and employees manage and calculate salary advances and personal loans. It provides a user-friendly interface for both backend and frontend operations, including loan eligibility checks, amortization schedules, and persistent loan records.

The application is split into two main components:
- **Backend**: Powered by FastAPI, responsible for all calculation logic, loan processing, and data persistence.
- **Frontend**: Built with Streamlit, providing an interactive web interface for users to request salary advances, personal loans, and view loan records.

---

## Features

- **Salary Advance Eligibility**: Check if an employee qualifies for a salary advance based on salary data and configurable criteria.
- **Personal Loan Calculator**: Calculate total repayable amount, and generate a full amortization schedule for personal loans.
- **Data Persistence**: All loans and advances are recorded in a CSV file for future reference.
- **Admin/HR Interface**: View all recorded loans, download amortization schedules, and manage loan history.

---

## Project Structure

```
advance_loan_calc/
├── back_end/
│   ├── fast_api_main.py       # FastAPI application
│   ├── calculations.py        # Core calculation logic
│   ├── requirements.txt       # Backend dependencies
│   └── Dockerfile             # Backend container setup
├── front_end/
│   ├── streamlit_main.py      # Streamlit application
│   ├── requirements.txt       # Frontend dependencies
│   └── Dockerfile             # Frontend container setup
├── data/
│   └── loans.csv              # CSV file storing all loan records
├── docker-compose.yaml        # Docker Compose setup
```

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) (recommended)
- Or Python 3.12+ and pip

---

### Running with Docker Compose (Recommended)

From the root of the repository, simply run:

```bash
docker compose up --build
```

This will:
- Build both the backend (FastAPI) and frontend (Streamlit) images.
- Start both services and connect them via a shared Docker network.
- Mount a shared volume for persistent loan records.

- The frontend (web UI) will be available at: `http://localhost:8501`

To stop the services, press <kbd>Ctrl+C</kbd> in your terminal and run:
```bash
docker compose down
```

---

### Running Locally (Without Docker)

#### Backend

```bash
cd back_end
pip install -r requirements.txt
fastapi run fast_api_main.py
```

#### Frontend

```bash
cd ../front_end
pip install -r requirements.txt
streamlit run streamlit_main.py
```

---

## Usage

1. **Open the Streamlit Frontend:**  
   Visit `http://localhost:8501` in your browser.

2. **Salary Advance:**  
   - Enter employee details and requested advance amount.
   - Check eligibility and process requests.

3. **Personal Loan:**  
   - Enter loan details such as amount, interest rate, and term.
   - View calculated repayment amounts and amortization schedule.

4. **Loan Records:**  
   - List all recorded loans.
   - Download amortization schedules as CSV.

---

## API Endpoints (Backend)

- `POST /calculate_advance`: Calculate and record salary advance eligibility.
- `POST /calculate_loan`: Calculate and record a personal loan, providing repayment schedule.
- `GET /loans`: Retrieve all recorded loans.

---

## Technologies Used

- Python 3.12
- FastAPI
- Streamlit
- Pandas
- Docker

---

## Contributing

Feel free to fork the repository, make changes, and open a pull request.

---

## License

This project is licensed under the MIT License.

---

## Author

- [TReV-89](https://github.com/TReV-89)