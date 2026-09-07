# Passman 🔐

A secure, cross-platform password manager to store and manage your credentials with end-to-end encryption. [Live](https://passman.letsgetthis.tech/)

---

## 🚀 Features

- **User Authentication & Authorization** 🛡️  
  – Sign up, log in, and manage sessions with JWT & Spring Security.  
- **End-to-End Encryption** 🔐  
  – AES encryption in the client ensures passwords are never sent or stored in plaintext.  
- **CRUD Password Entries** ✏️🗑️  
  – Create, read, update, and delete secure password records.  
- **Cross-Platform Desktop Client** 💻  
  – Built with React + Vite wrapped in Tauri (Rust) for native performance on Windows, macOS & Linux.  
- **Responsive & Modular UI** 🎨  
  – Component-based React with CSS Modules for scoped styling and easy theming.

---

## 📸 Screenshots

### Home Screen
![image](https://github.com/user-attachments/assets/c2fe87b7-7325-4e66-b65d-e81bcaf58ba5)


### Login Screen  
![image](https://github.com/user-attachments/assets/139ff943-bf24-4d5b-a013-f1976445a433)



### Sign Up  
![image](https://github.com/user-attachments/assets/9a734046-6a89-40d3-9fde-2e3538ef128e)


### Dashboard / Password List  
![image](https://github.com/user-attachments/assets/ab3462da-956a-4fcd-880e-a18dcc100bd3)

---

## ⚙️ Installation & Setup

### Backend (Spring Boot)

1. **Prerequisites:**  
   - Java 11+  
   - Maven 3.6+  
   - MySQL (or H2 for in-memory testing)

2. **Clone & Build:**
   ```bash
   git clone https://github.com/aabhi-k/passman.git
   cd passman/backend
   mvn clean install
   ```

3. **Configure Database:**  
   - Edit `src/main/resources/application.yml` with your DB credentials.

4. **Run Server:**
   ```bash
   mvn spring-boot:run
   ```

### Frontend (React + Tauri)

1. **Prerequisites:**  
   - Node.js 16+ & npm/yarn  
   - Rust & Cargo (for Tauri)

2. **Install Dependencies:**
   ```bash
   cd ../frontend
   npm install
   # or
   yarn install
   ```

3. **Run in Dev Mode:**
   ```bash
   npm run tauri dev
   # or
   yarn tauri dev
   ```

4. **Build for Production:**
   ```bash
   npm run tauri build
   # or
   yarn tauri build
   ```

---

## ⚙️ Usage

1. Launch the desktop client.  
2. Register a new account or log in.  
3. Add, view, edit, or delete your password entries securely.  
4. Enjoy peace of mind knowing your data is protected!

---

## 🧰 Tech Stack

- **Backend:** Java, Spring Boot, Spring Security, JWT, Hibernate/JPA, MySQL/H2  
- **Frontend:** React, Vite, CSS Modules  
- **Desktop Wrapper:** Tauri (Rust)  
- **Encryption:** Web Crypto API (AES)

---

## 🤝 Contributing

1. Fork the repository  
2. Create your feature branch (`git checkout -b feature/YourFeature`)  
3. Commit your changes (`git commit -m 'Add some feature'`)  
4. Push to the branch (`git push origin feature/YourFeature`)  
5. Open a Pull Request

---
