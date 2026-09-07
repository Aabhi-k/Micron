package com.aabhi.pasman.service.authservice;

import com.aabhi.pasman.dto.auth.LoginDto;
import com.aabhi.pasman.dto.auth.LoginResponseDto;
import com.aabhi.pasman.dto.auth.UserDto;
import com.aabhi.pasman.exception.exceptions.AuthenticationFailedException;
import com.aabhi.pasman.exception.exceptions.InvalidUserDataException;
import com.aabhi.pasman.exception.exceptions.UserAlreadyExistsException;
import com.aabhi.pasman.model.User;
import com.aabhi.pasman.repository.UserRepository;
import com.aabhi.pasman.security.jwt.JwtService;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.util.Base64;
import java.util.Optional;

@Service
public class AuthServiceImpl implements AuthService {

    private final UserRepository userRepository;
    private final AuthenticationManager authenticationManager;
    private final BCryptPasswordEncoder bCryptPasswordEncoder;
    private final JwtService jwtService;

    public AuthServiceImpl(UserRepository userRepository, AuthenticationManager authenticationManager, BCryptPasswordEncoder bCryptPasswordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.authenticationManager = authenticationManager;
        this.bCryptPasswordEncoder = bCryptPasswordEncoder;
        this.jwtService = jwtService;
    }

    @Override
    public LoginResponseDto login(LoginDto loginDto) {
        try {
            // Validate input data first
            if (loginDto.getEmail() == null || loginDto.getPassword() == null) {
                throw new InvalidUserDataException("Email and password are required");
            }
            
            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(
                            loginDto.getEmail(),
                            loginDto.getPassword()
                    )
            );
            
            User authenticatedUser = userRepository.findByEmail(loginDto.getEmail())
                    .orElseThrow(() -> new AuthenticationFailedException("User not found"));

            String token = jwtService.generateToken(authenticatedUser);

            return LoginResponseDto.builder()
                    .token(token)
                    .encryptionSalt(authenticatedUser.getEncryptionSalt())
                    .userId(authenticatedUser.getId())
                    .build();
                    
        } catch (AuthenticationException e) {
            throw new AuthenticationFailedException("Invalid email or password");
        }
    }

    @Override
    public LoginResponseDto register(UserDto userDto) {
        // Validate input data
        if (userDto.getName() == null || userDto.getEmail() == null || userDto.getPassword() == null) {
            throw new InvalidUserDataException("Username, email, and password are required");
        }

        String name = userDto.getName();
        String email = userDto.getEmail();
        String rawPassword = userDto.getPassword();

        // Validate email format
        String emailRegex = "(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])+)\\])";
        if (!email.matches(emailRegex)) {
            throw new InvalidUserDataException("Invalid email format");
        }

        // Validate username format
        String usernameRegex = "^[a-zA-Z0-9]*$";
        if (!name.matches(usernameRegex)) {
            throw new InvalidUserDataException("Username must contain only letters and numbers");
        }

        // Validate password length
        if (rawPassword.length() < 8) {
            throw new InvalidUserDataException("Password must be at least 8 characters long");
        }

        // Check if user already exists
        Optional<User> existingUser = userRepository.findByEmail(email);
        if (existingUser.isPresent()) {
            throw new UserAlreadyExistsException("User with this email already exists");
        }

        // Generate encryption salt and hash password
        String password = bCryptPasswordEncoder.encode(rawPassword);
        String encryptionSalt = AESKeyUtils.generateSalt();

        // Create and save user
        try {
            User user = User.builder()
                    .name(name)
                    .password(password)
                    .email(email)
                    .encryptionSalt(encryptionSalt)
                    .build();

            User savedUser = userRepository.save(user);
            String token = jwtService.generateToken(savedUser);
            
            return LoginResponseDto.builder()
                    .token(token)
                    .encryptionSalt(encryptionSalt)
                    .userId(savedUser.getId())
                    .build();
                    
        } catch (Exception e) {
            throw new RuntimeException("Error creating user: " + e.getMessage());
        }
    }

    @Override
    public boolean checkUser(String id) {
        if (id == null || id.trim().isEmpty()) {
            return false;
        }
        
        Optional<User> user = userRepository.findById(id);
        return user.isPresent();
    }

    @Override
    public User getUserById(String id) {
        if (id == null || id.trim().isEmpty()) {
            throw new InvalidUserDataException("User ID cannot be empty");
        }
        
        return userRepository.findById(id)
                .orElseThrow(() -> new AuthenticationFailedException("User not found"));
    }

    @Override
    public void changePassword(UserDto userDto) {
        // Validate input data
        if (userDto.getId() == null || userDto.getPassword() == null) {
            throw new InvalidUserDataException("User ID and new password are required");
        }

        String userId = userDto.getId();
        String newPassword = userDto.getPassword();

        // Validate password length
        if (newPassword.length() < 8) {
            throw new InvalidUserDataException("Password must be at least 8 characters long");
        }

        // Find user by ID
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new AuthenticationFailedException("User not found"));

        // Hash the new password
        String hashedPassword = bCryptPasswordEncoder.encode(newPassword);

        // Update user's password
        user.setPassword(hashedPassword);

        // Save updated user
        userRepository.save(user);
    }
}

class AESKeyUtils {
    public static String generateSalt() {
        byte[] salt = new byte[16]; // 128-bit salt
        new SecureRandom().nextBytes(salt);
        return Base64.getEncoder().encodeToString(salt);
    }
}

