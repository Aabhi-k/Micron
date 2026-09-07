package com.aabhi.pasman.service.authservice;

import com.aabhi.pasman.dto.auth.LoginDto;
import com.aabhi.pasman.dto.auth.LoginResponseDto;
import com.aabhi.pasman.dto.auth.UserDto;
import com.aabhi.pasman.model.User;

public interface AuthService {
    LoginResponseDto login(LoginDto loginDto);

    LoginResponseDto register(UserDto userDto);

    boolean checkUser(String id);
    User getUserById(String id);

    void changePassword(UserDto userDto);
}
