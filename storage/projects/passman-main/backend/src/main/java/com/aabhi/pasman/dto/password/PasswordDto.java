package com.aabhi.pasman.dto.password;

import lombok.*;

@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
@ToString
public class PasswordDto {
    private String encryptedData;
    private String iv;
    private String authTag;
    private String userId;
}
