package com.aabhi.pasman.service.passwordservice;

import com.aabhi.pasman.dto.password.PasswordDto;
import com.aabhi.pasman.dto.password.PasswordResponseDto;
import com.aabhi.pasman.exception.exceptions.InvalidPasswordDataException;
import com.aabhi.pasman.exception.exceptions.PasswordNotFoundException;
import com.aabhi.pasman.model.Password;
import com.aabhi.pasman.repository.PasswordRepository;
import com.aabhi.pasman.service.authservice.AuthService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.List;

@Service
public class PasswordServiceImpl implements PasswordService {
    private final PasswordRepository passwordRepository;
    private final AuthService authService;

    @Autowired
    public PasswordServiceImpl(PasswordRepository passwordRepository, AuthService authService) {
        this.passwordRepository = passwordRepository;
        this.authService = authService;
    }

    @Override
    public void insertPassword(PasswordDto passwordDto) {
       String userId = passwordDto.getUserId();
       if (userId == null) {
           throw new InvalidPasswordDataException("User ID is null");
       } else if (!authService.checkUser(userId)) {
           throw new InvalidPasswordDataException("User not found");
       }
       
       // Validate required password data
       if (passwordDto.getEncryptedData() == null || passwordDto.getEncryptedData().isEmpty()) {
           throw new InvalidPasswordDataException("Encrypted data cannot be empty");
       }
       if (passwordDto.getIv() == null || passwordDto.getIv().isEmpty()) {
           throw new InvalidPasswordDataException("IV cannot be empty");
       }
       if (passwordDto.getAuthTag() == null || passwordDto.getAuthTag().isEmpty()) {
           throw new InvalidPasswordDataException("Auth tag cannot be empty");
       }
       
       Password password = toPassword(passwordDto);
       passwordRepository.save(password);
    }

    @Override
    public PasswordResponseDto getPassword(String passwordId) {
        if (passwordId == null) {
            throw new InvalidPasswordDataException("Password ID is null");
        }
        return passwordRepository.findById(passwordId)
            .map(this::toPasswordDto)
            .orElseThrow(() -> new PasswordNotFoundException("Password not found with ID: " + passwordId));
    }

    @Override
    public void updatePassword(PasswordDto passwordDto, String passwordId) {
        if (passwordId == null) {
            throw new InvalidPasswordDataException("Password ID is null");
        }
        
        Password password = passwordRepository.findById(passwordId)
            .orElseThrow(() -> new PasswordNotFoundException("Password not found with ID: " + passwordId));
        
        boolean isModified = false;
        
        if (passwordDto.getEncryptedData() != null) {
            password.setEncryptedData(passwordDto.getEncryptedData());
            isModified = true;
        }
        if (passwordDto.getIv() != null) {
            password.setIv(passwordDto.getIv());
            isModified = true;
        }
        if (passwordDto.getAuthTag() != null) {
            password.setAuthTag(passwordDto.getAuthTag());
            isModified = true;
        }
        
        if (!isModified) {
            throw new InvalidPasswordDataException("No data provided for update");
        }
        
        password.setUpdatedAt(new Date());
        passwordRepository.save(password);
    }

    @Override
    public String deletePassword(String passwordId) {
        if(passwordId == null) {
            throw new InvalidPasswordDataException("Password ID is null");
        }
        
        if(!passwordRepository.existsById(passwordId)) {
            throw new PasswordNotFoundException("Password not found with ID: " + passwordId);
        }
        
        passwordRepository.deleteById(passwordId);
        return "Password deleted successfully";
    }

    @Override
    public List<PasswordResponseDto> getAllPasswords(String userId) {
        if (userId == null) {
            throw new InvalidPasswordDataException("User ID is null");
        }
        
        if (!authService.checkUser(userId)) {
            throw new InvalidPasswordDataException("User not found with ID: " + userId);
        }

        List<Password> passwords = passwordRepository.findByUserId(userId);
        
        return passwords.stream()
                .map(this::toPasswordDto)
                .toList();
    }

    // Mappers
    public PasswordResponseDto toPasswordDto(Password password) {
        return PasswordResponseDto.builder()
                .id(password.getId())
                .encryptedData(password.getEncryptedData())
                .iv(password.getIv())
                .authTag(password.getAuthTag())
                .userId(password.getUser().getId())
                .createdAt(password.getCreatedAt().getTime())
                .updatedAt(password.getUpdatedAt().getTime())
                .build();
    }
    public Password toPassword(PasswordDto passwordDto) {
        return Password.builder()
                .encryptedData(passwordDto.getEncryptedData())
                .iv(passwordDto.getIv())
                .authTag(passwordDto.getAuthTag())
                .user(authService.getUserById(passwordDto.getUserId()))
                .createdAt(new Date())
                .updatedAt(new Date())
                .build();
    }

}


