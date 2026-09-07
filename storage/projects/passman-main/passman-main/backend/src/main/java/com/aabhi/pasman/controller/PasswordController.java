package com.aabhi.pasman.controller;

import com.aabhi.pasman.dto.password.PasswordDto;
import com.aabhi.pasman.dto.password.PasswordResponseDto;
import com.aabhi.pasman.service.passwordservice.PasswordService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/passwords")
public class PasswordController {

    private final PasswordService passwordService;

    public PasswordController(PasswordService passwordService) {
        this.passwordService = passwordService;
    }

    @PostMapping("/insert")
    public ResponseEntity<String> insertPassword(@RequestBody PasswordDto passwordDto) {
        passwordService.insertPassword(passwordDto);
        return ResponseEntity.status(HttpStatus.CREATED).body("Password inserted successfully");
    }

    @GetMapping("/getall/{userId}")
    public ResponseEntity<List<PasswordResponseDto>> getAllPasswords(@PathVariable String userId) {
        List<PasswordResponseDto> passwords = passwordService.getAllPasswords(userId);
        return ResponseEntity.ok(passwords);
    }

    @GetMapping("/get/{passwordId}")
    public ResponseEntity<PasswordResponseDto> getPassword(@PathVariable String passwordId) {
        PasswordResponseDto passwordDto = passwordService.getPassword(passwordId);
        return ResponseEntity.ok(passwordDto);
    }

    @PutMapping("/update/{passwordId}")
    public ResponseEntity<String> updatePassword(@RequestBody PasswordDto passwordDto, @PathVariable String passwordId) {
        passwordService.updatePassword(passwordDto, passwordId);
        return ResponseEntity.ok("Password updated successfully");
    }

    @DeleteMapping("/delete/{passwordId}")
    public ResponseEntity<String> deletePassword(@PathVariable String passwordId) {
        String response = passwordService.deletePassword(passwordId);
        return ResponseEntity.ok(response);
    }
}
