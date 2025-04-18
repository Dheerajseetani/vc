# VC Tracker

A secure web application for tracking Venture Capital (VC) investments and payments.

## Features

- User authentication with secure password hashing
- Personal VC tracking
- Payment history management
- Interest rate calculations
- Profit analysis
- Historical data support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vc_tracker.git
cd vc_tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```
SECRET_KEY=your_secret_key_here
```

## Usage

1. Start the application:
```bash
streamlit run app/main.py
```

2. Access the application at `http://localhost:8501`

3. Register a new account or login with existing credentials

4. Start tracking your VCs!

## Project Structure

```
vc_tracker/
├── app/
│   ├── main.py           # Main application file
│   ├── auth.py           # Authentication utilities
│   └── vc_manager.py     # VC management functions
├── data/
│   └── users.json        # User data storage
├── utils/
│   └── helpers.py        # Helper functions
├── requirements.txt      # Project dependencies
├── .gitignore           # Git ignore file
└── README.md            # Project documentation
```

## Security

- Passwords are hashed using bcrypt
- User data is stored securely
- Session management for authenticated users
- Environment variables for sensitive data

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 