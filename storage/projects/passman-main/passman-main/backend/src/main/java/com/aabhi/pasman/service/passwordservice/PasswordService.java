package com.aabhi.pasman.service.passwordservice;

import com.aabhi.pasman.dto.password.PasswordDto;
import com.aabhi.pasman.dto.password.PasswordResponseDto;

import java.util.List;

public interface PasswordService {
    void insertPassword(PasswordDto passwordDto) ;
    PasswordResponseDto getPassword(String passwordId) ;
    void updatePassword(PasswordDto passwordDto, String passwordId) ;
    String deletePassword(String passwordId) ;
    List<PasswordResponseDto> getAllPasswords(String userId);

}
