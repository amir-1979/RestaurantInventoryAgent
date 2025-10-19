# 🔐 Secure Restaurant Inventory Dashboard

A secure, login-protected inventory management system with role-based access control.

## 🚀 Quick Start

### 1. Launch the Secure Dashboard
```bash
python run_dashboard.py
```
This will start the secure dashboard with login protection.

### 2. Default Login Credentials
For demo purposes, these default accounts are created:


### 3. Access the Dashboard
1. Open your browser to `http://localhost:8501`
2. Enter username and password
3. Click "Login" to access the inventory system

## 🛡️ Security Features

### ✅ **Authentication**
- Secure login system with hashed passwords
- Session management with automatic logout
- Protection against unauthorized access

### ✅ **Role-Based Access**
- **Admin**: Full access + user management
- **Manager**: Full inventory access
- **Staff**: Basic inventory viewing

### ✅ **Data Protection**
- Passwords are hashed using SHA-256
- Session state management
- Secure file handling

## 👥 User Management

### Using the Setup Script
```bash
python setup_users.py
```

This interactive script allows you to:
- Add new users
- List existing users
- Delete users
- Reset passwords
- Create default demo users

### Admin Panel
Admins can manage users directly from the dashboard:
1. Login as admin
2. Go to "User Management" tab
3. Add new users with username/password

## 🎛️ Dashboard Options

### Secure Dashboard (Default)
```bash
python run_dashboard.py
```
- Login required
- Role-based access
- User management for admins

### Skip Authentication
```bash
python run_dashboard.py --no-auth
```
- Direct access without login
- Uses ultra-safe dashboard

### Other Versions
```bash
# Full version with AI features
python run_dashboard.py --full

# Simple version
python run_dashboard.py --simple

# Bulletproof version
python run_dashboard.py --bulletproof
```

## 📊 Features

### **Dashboard Capabilities**
- Real-time inventory metrics
- Interactive charts (if Plotly available)
- Expired/expiring/fresh item analysis
- Smart recommendations
- CSV export functionality

### **Security Features**
- Session timeout protection
- Secure password storage
- User activity tracking
- Role-based data access

### **User Experience**
- Clean, intuitive interface
- Mobile-responsive design
- Real-time data updates
- Comprehensive error handling

## 🔧 Configuration

### User Storage
Users are stored in `users.json` with hashed passwords:
```json
{
  "admin": "hashed_password_here",
  "manager": "hashed_password_here"
}
```

### Customization
You can modify:
- Default users in `secure_dashboard.py`
- Password requirements
- Session timeout settings
- Role permissions

## 🛠️ Troubleshooting

### Login Issues
1. **Invalid credentials**: Check username/password
2. **Session expired**: Refresh page and login again
3. **Users file missing**: Run `python setup_users.py` to create users

### Dashboard Issues
1. **CSV not found**: Ensure `inventory.csv` exists
2. **Charts not showing**: Install plotly: `pip install plotly`
3. **Permission errors**: Check file permissions

## 📁 File Structure

```
├── secure_dashboard.py      # Main secure dashboard
├── setup_users.py          # User management script
├── users.json              # User credentials (auto-created)
├── inventory.csv           # Inventory data
├── run_dashboard.py        # Launcher script
└── README_SECURE.md        # This file
```

## 🔒 Production Deployment

For production use:

1. **Change default passwords**
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** for web deployment
4. **Set up proper database** instead of JSON files
5. **Implement session timeouts**
6. **Add audit logging**

## 💡 Tips

- **Admin users** can manage other users
- **CSV exports** include timestamps
- **Session data** persists during browser session
- **Logout** clears all session data
- **Role permissions** can be customized in code

## 🆘 Support

If you encounter issues:
1. Check the console for error messages
2. Verify `inventory.csv` format
3. Ensure all dependencies are installed
4. Try the `--no-auth` option for testing

---

**Security Note**: This is a demo implementation. For production use, implement proper authentication systems, database storage, and security best practices.