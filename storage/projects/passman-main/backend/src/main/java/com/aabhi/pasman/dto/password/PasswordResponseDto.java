package com.aabhi.pasman.dto.password;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder

public class PasswordResponseDto {
    private String id;
    private String encryptedData;
    private String iv;
    private String authTag;
    private String userId;
    private long createdAt;
    private long updatedAt;
}
