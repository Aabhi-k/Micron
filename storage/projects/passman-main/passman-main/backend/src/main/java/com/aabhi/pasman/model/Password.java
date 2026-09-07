package com.aabhi.pasman.model;

import jakarta.persistence.*;
import lombok.*;

import java.util.Date;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder

@Entity
@Table(name = "passwords")
public class Password {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;
    @Lob
    @Column(nullable = false)
    private String encryptedData;
    @Column(nullable = false)
    private String iv; // Base64-encoded IV used during encryption

    @Column(nullable = false)
    private String authTag; // Base64-encoded AES-GCM auth tag

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    private Date createdAt;
    private Date updatedAt;



}