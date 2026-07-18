"""Auth code generator — generates authentication code."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.generators.base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class AuthGenerator(BaseGenerator):
    """Generates authentication endpoints and UI."""

    def generate_backend_auth(self) -> list[Path]:
        """Generate backend authentication code."""
        created = []

        created.append(self.write_file("backend/app/api/v1/auth.py", self._get_auth_endpoints()))
        created.append(self.write_file("backend/app/schemas/auth.py", self._get_auth_schemas()))
        created.append(self.write_file("backend/app/services/auth_service.py", self._get_auth_service()))

        logger.info("Generated backend authentication code")
        return created

    def generate_frontend_auth(self) -> list[Path]:
        """Generate frontend authentication UI."""
        created = []

        created.append(self.write_file("frontend/lib/features/auth/login_screen.dart", self._get_login_screen()))
        created.append(self.write_file("frontend/lib/features/auth/register_screen.dart", self._get_register_screen()))
        created.append(self.write_file("frontend/lib/core/providers/auth_provider.dart", self._get_auth_provider()))

        logger.info("Generated frontend authentication code")
        return created

    def _get_auth_endpoints(self) -> str:
        return '''"""Auth API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        _, _, access_token, refresh_token = await service.register(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(request.email, request.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user, access_token, refresh_token = result
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
'''

    def _get_auth_schemas(self) -> str:
        return '''"""Auth schemas."""
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
'''

    def _get_auth_service(self) -> str:
        return '''"""Auth service."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import hash_password, verify_password, create_token

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, full_name: str) -> tuple:
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
        self.db.add(user)
        await self.db.flush()

        access_token = create_token(str(user.id))
        return user, None, access_token, access_token

    async def login(self, email: str, password: str) -> tuple | None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            return None
        access_token = create_token(str(user.id))
        return user, access_token, access_token
'''

    def _get_login_screen(self) -> str:
        return '''"""Login screen."""
import 'package:flutter/material.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text("Welcome Back", style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _emailController,
                  decoration: const InputDecoration(labelText: "Email"),
                  keyboardType: TextInputType.emailAddress,
                  validator: (v) => v?.contains("@") == true ? null : "Invalid email",
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  decoration: const InputDecoration(labelText: "Password"),
                  obscureText: true,
                  validator: (v) => (v?.length ?? 0) >= 6 ? null : "Too short",
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {},
                    child: const Text("Login"),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
'''

    def _get_register_screen(self) -> str:
        return '''import 'package:flutter/material.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Create Account")),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            TextField(controller: _nameController, decoration: const InputDecoration(labelText: "Full Name")),
            const SizedBox(height: 16),
            TextField(controller: _emailController, decoration: const InputDecoration(labelText: "Email")),
            const SizedBox(height: 16),
            TextField(controller: _passwordController, decoration: const InputDecoration(labelText: "Password"), obscureText: true),
            const SizedBox(height: 24),
            ElevatedButton(onPressed: () {}, child: const Text("Register")),
          ],
        ),
      ),
    );
  }
}
'''

    def _get_auth_provider(self) -> str:
        return """import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(apiClientProvider));
});

class AuthState {
  final bool isAuthenticated;
  final String? token;
  final String? email;

  const AuthState({this.isAuthenticated = false, this.token, this.email});
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _api;

  AuthNotifier(this._api) : super(const AuthState());

  Future<void> login(String email, String password) async {
    try {
      final response = await _api.post('/auth/login', data: {
        'email': email,
        'password': password,
      });
      final token = response.data['access_token'] as String;
      _api.setToken(token);
      state = AuthState(isAuthenticated: true, token: token, email: email);
    } catch (e) {
      rethrow;
    }
  }

  void logout() {
    _api.clearToken();
    state = const AuthState();
  }
}
"""
