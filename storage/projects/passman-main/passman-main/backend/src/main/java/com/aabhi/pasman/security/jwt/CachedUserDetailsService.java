package com.aabhi.pasman.security.jwt;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class CachedUserDetailsService implements UserDetailsService {

    private final UserDetailsService userDetailsService;
    private final Map<String, UserDetails> cache = new HashMap<>();

    public CachedUserDetailsService(UserDetailsService userDetailsService) {
        this.userDetailsService = userDetailsService;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        return cache.computeIfAbsent(username, userDetailsService::loadUserByUsername);
    }
}