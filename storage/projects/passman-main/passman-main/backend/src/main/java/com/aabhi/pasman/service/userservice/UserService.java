package com.aabhi.pasman.service.userservice;

import com.aabhi.pasman.dto.user.ChangePasswordDTO;
import com.aabhi.pasman.dto.user.UpdateUserDTO;
import com.aabhi.pasman.dto.user.UserDetailsDTO;

public interface UserService {
    UserDetailsDTO getCurrentUserDetails();
    UserDetailsDTO updateUserDetails(UpdateUserDTO updateUserDTO);
    void changePassword(ChangePasswordDTO changePasswordDTO);
}