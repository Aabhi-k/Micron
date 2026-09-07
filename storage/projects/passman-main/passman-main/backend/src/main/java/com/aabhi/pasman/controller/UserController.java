package com.aabhi.pasman.controller;

import com.aabhi.pasman.dto.user.ChangePasswordDTO;
import com.aabhi.pasman.dto.user.UpdateUserDTO;
import com.aabhi.pasman.dto.user.UserDetailsDTO;
import com.aabhi.pasman.service.userservice.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/user")
public class UserController {

    private final UserService userService;

    @Autowired
    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/details")
    public ResponseEntity<UserDetailsDTO> getUserDetails() {
        UserDetailsDTO userDetails = userService.getCurrentUserDetails();
        return ResponseEntity.ok(userDetails);
    }

    @PutMapping("/update")
    public ResponseEntity<UserDetailsDTO> updateUser(@RequestBody UpdateUserDTO updateUserDTO) {
        UserDetailsDTO updatedUser = userService.updateUserDetails(updateUserDTO);
        return ResponseEntity.ok(updatedUser);
    }

    @PostMapping("/change-password")
    public ResponseEntity<Void> changePassword(@RequestBody ChangePasswordDTO changePasswordDTO) {
        userService.changePassword(changePasswordDTO);
        return ResponseEntity.ok().build();
    }
}