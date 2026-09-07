package com.aabhi.pasman.repository;

import com.aabhi.pasman.model.Password;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PasswordRepository extends JpaRepository<Password, String> {
    // Custom query methods can be defined here if needed
    // For example, find by userId or any other criteria
    List<Password> findByUserId(String userId);
}
