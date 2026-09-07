package com.aabhi.pasman.service.userservice;

import com.aabhi.pasman.dto.user.ChangePasswordDTO;
import com.aabhi.pasman.dto.user.UpdateUserDTO;
import com.aabhi.pasman.dto.user.UserDetailsDTO;
import com.aabhi.pasman.exception.exceptions.BadRequestException;
import com.aabhi.pasman.exception.exceptions.ResourceNotFoundException;
import com.aabhi.pasman.model.User;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import com.aabhi.pasman.repository.UserRepository;

@Service
public class UserServiceImpl implements UserService {
    private final UserRepository userRepository;
    private final BCryptPasswordEncoder passwordEncoder;

    @Autowired
    public UserServiceImpl(UserRepository userRepository, BCryptPasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public UserDetailsDTO getCurrentUserDetails() {
        User user = getCurrentUser();
        return mapToUserDetailsDTO(user);
    }

    @Override
    @Transactional
    public UserDetailsDTO updateUserDetails(UpdateUserDTO updateUserDTO) {
        User user = getCurrentUser();

        // Check if email is being changed and if it's already in use
        if (!user.getEmail().equals(updateUserDTO.getEmail()) &&
                userRepository.existsByEmail(updateUserDTO.getEmail())) {
            throw new BadRequestException("Email is already in use");
        }

        user.setName(updateUserDTO.getName());
        user.setEmail(updateUserDTO.getEmail());
        User savedUser = userRepository.save(user);

        return mapToUserDetailsDTO(savedUser);
    }

    @Override
    @Transactional
    public void changePassword(ChangePasswordDTO changePasswordDTO) {
        User user = getCurrentUser();

        // Verify current password
        if (!passwordEncoder.matches(changePasswordDTO.getCurrentPassword(), user.getPassword())) {
            throw new BadCredentialsException("Current password is incorrect");
        }

        // Verify new password matches confirmation
        if (!changePasswordDTO.getNewPassword().equals(changePasswordDTO.getConfirmPassword())) {
            throw new BadRequestException("New password and confirm password do not match");
        }

        // Update password

        System.out.println(changePasswordDTO.getNewPassword());
        user.setPassword(passwordEncoder.encode(changePasswordDTO.getNewPassword()));
        userRepository.save(user);
    }

    private User getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String email = authentication.getName();
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
    }
    
    private UserDetailsDTO mapToUserDetailsDTO(User user) {
        return UserDetailsDTO.builder()
                .id(user.getId())
                .name(user.getName())
                .email(user.getEmail())
                .build();
    }
}