<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { authState, checkSession, signOut, type User as AuthUser } from '$lib/auth';

	interface User {
		id: string;
		email: string;
		name: string;
		created_at: string;
	}

	interface UserRegistration {
		email: string;
		name: string;
		password: string;
		password_confirm: string;
	}

	let apiStatus: 'checking' | 'connected' | 'disconnected' = 'checking';
	let apiMessage = '';
	let users: User[] = [];
	let loadingUsers = false;
	let showAddUserForm = false;
	let submittingUser = false;
	let message = '';
	let messageType: 'success' | 'error' | '' = '';

	// Form data
	let formData: UserRegistration = {
		email: '',
		name: '',
		password: '',
		password_confirm: ''
	};

	onMount(async () => {
		// Check authentication first
		const auth = await checkSession();
		if (!auth.authenticated) {
			goto('/login');
			return;
		}
		
		await checkApiStatus();
		if (apiStatus === 'connected') {
			await loadUsers();
		}
	});

	async function checkApiStatus() {
		try {
			const isHealthy = await api.healthCheck();
			if (isHealthy) {
				apiStatus = 'connected';
				apiMessage = 'Successfully connected to backend API';
			} else {
				apiStatus = 'disconnected';
				apiMessage = 'Backend API is not responding correctly';
			}
		} catch (error) {
			apiStatus = 'disconnected';
			apiMessage = `Failed to connect to backend: ${error}`;
		}
	}

	async function loadUsers() {
		loadingUsers = true;
		console.log('Starting to load users...');
		try {
			console.log('Making API call to /users');
			const response = await api.get<User[]>('/users');
			console.log('API response:', response);
			if (response.data) {
				users = response.data;
				console.log('Successfully loaded users:', users);
			} else {
				console.error('Failed to load users:', response.error);
				setMessage(`Failed to load users: ${response.error}`, 'error');
			}
		} catch (error) {
			console.error('Error loading users:', error);
			setMessage(`Error loading users: ${error}`, 'error');
		} finally {
			loadingUsers = false;
			console.log('Finished loading users, count:', users.length);
		}
	}

	async function handleSubmit() {
		if (formData.password !== formData.password_confirm) {
			setMessage('Passwords do not match', 'error');
			return;
		}

		submittingUser = true;
		setMessage('', '');

		try {
			const response = await api.post<User, UserRegistration>('/users/register', formData);
			if (response.data) {
				setMessage('User created successfully!', 'success');
				// Reset form
				formData = { email: '', name: '', password: '', password_confirm: '' };
				showAddUserForm = false;
				// Reload users list
				await loadUsers();
			} else {
				setMessage(response.error || 'Failed to create user', 'error');
			}
		} catch (error) {
			setMessage('An unexpected error occurred', 'error');
		} finally {
			submittingUser = false;
		}
	}

	function setMessage(text: string, type: 'success' | 'error' | '') {
		message = text;
		messageType = type;
		if (text) {
			setTimeout(() => {
				message = '';
				messageType = '';
			}, 5000);
		}
	}

	const getStatusColor = (status: typeof apiStatus) => {
		switch (status) {
			case 'connected': return '#22c55e';
			case 'disconnected': return '#ef4444';
			case 'checking': return '#f59e0b';
		}
	};

	const getStatusIcon = (status: typeof apiStatus) => {
		switch (status) {
			case 'connected': return '✅';
			case 'disconnected': return '❌';
			case 'checking': return '⏳';
		}
	};

	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString();
	}
</script>

<svelte:head>
	<title>Acro Planner Admin</title>
	<meta name="description" content="Admin interface for Acro Planner" />
</svelte:head>

<div class="container">
	<header>
		<div class="header-content">
			<div>
				<h1>🤸‍♀️ Acro Planner Admin</h1>
				<p>Administrative interface for managing the Acro Planner application</p>
			</div>
			<div class="user-info">
				{#if $authState.authenticated && $authState.user}
					<div class="user-card">
						{#if $authState.user.image}
							<img src={$authState.user.image} alt="User avatar" class="user-avatar" />
						{:else}
							<div class="user-avatar-placeholder">
								{$authState.user.name?.charAt(0).toUpperCase() || '?'}
							</div>
						{/if}
						<div class="user-details">
							<div class="user-name">{$authState.user.name}</div>
							<div class="user-email">{$authState.user.email}</div>
						</div>
					</div>
					<button class="logout-btn" on:click={signOut}>
						Sign Out
					</button>
				{:else}
					<div class="auth-actions">
						<a href="/login" class="login-btn">Sign In</a>
					</div>
				{/if}
			</div>
		</div>
	</header>

	<main>
		<section class="status-section">
			<h2>System Status</h2>
			<div class="status-card" style="border-left-color: {getStatusColor(apiStatus)}">
				<div class="status-header">
					<span class="status-icon">{getStatusIcon(apiStatus)}</span>
					<h3>Backend API</h3>
				</div>
				<p class="status-message">{apiMessage}</p>
				<small>API Endpoint: https://acro-planner-backend-733697808355.us-central1.run.app</small>
			</div>
		</section>

		{#if message}
			<div class="message message-{messageType}">
				{message}
			</div>
		{/if}

		<section class="users-section">
			<div class="section-header">
				<h2>👥 User Management</h2>
				<button class="primary-btn" on:click={() => showAddUserForm = !showAddUserForm}>
					{showAddUserForm ? 'Cancel' : 'Add New User'}
				</button>
			</div>

			{#if showAddUserForm}
				<div class="form-card">
					<h3>Add New User</h3>
					<form on:submit|preventDefault={handleSubmit}>
						<div class="form-group">
							<label for="email">Email:</label>
							<input 
								type="email" 
								id="email" 
								bind:value={formData.email} 
								required 
								disabled={submittingUser}
							/>
						</div>
						<div class="form-group">
							<label for="name">Name:</label>
							<input 
								type="text" 
								id="name" 
								bind:value={formData.name} 
								required 
								disabled={submittingUser}
							/>
						</div>
						<div class="form-group">
							<label for="password">Password:</label>
							<input 
								type="password" 
								id="password" 
								bind:value={formData.password} 
								required 
								minlength="8"
								disabled={submittingUser}
							/>
						</div>
						<div class="form-group">
							<label for="password_confirm">Confirm Password:</label>
							<input 
								type="password" 
								id="password_confirm" 
								bind:value={formData.password_confirm} 
								required 
								minlength="8"
								disabled={submittingUser}
							/>
						</div>
						<div class="form-actions">
							<button type="submit" class="submit-btn" disabled={submittingUser}>
								{submittingUser ? 'Creating...' : 'Create User'}
							</button>
						</div>
					</form>
				</div>
			{/if}

			<div class="users-list">
				{#if loadingUsers}
					<div class="loading">Loading users...</div>
				{:else if users.length === 0}
					<div class="empty-state">No users found</div>
				{:else}
					<div class="users-table">
						<div class="table-header">
							<div class="table-cell">Name</div>
							<div class="table-cell">Email</div>
							<div class="table-cell">Created</div>
						</div>
						{#each users as user}
							<div class="table-row">
								<div class="table-cell">{user.name}</div>
								<div class="table-cell">{user.email}</div>
								<div class="table-cell">{formatDate(user.created_at)}</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</section>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background-color: #f8fafc;
		color: #334155;
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	header {
		margin-bottom: 3rem;
	}
	
	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.user-info {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.user-card {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
		border: 1px solid #e2e8f0;
	}
	
	.user-avatar {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
	}

	.user-avatar-placeholder {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		background: #3b82f6;
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		font-size: 0.875rem;
	}
	
	.user-details {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	
	.user-name {
		font-weight: 600;
		font-size: 0.875rem;
		color: #1e293b;
	}
	
	.user-email {
		font-size: 0.75rem;
		color: #64748b;
	}
	
	.logout-btn {
		padding: 0.375rem 0.75rem;
		background: #ef4444;
		color: white;
		border: none;
		border-radius: 0.375rem;
		font-size: 0.75rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
	}
	
	.logout-btn:hover {
		background: #dc2626;
	}
	
	.auth-actions {
		display: flex;
		align-items: center;
	}
	
	.login-btn {
		padding: 0.5rem 1rem;
		background: #3b82f6;
		color: white;
		text-decoration: none;
		border-radius: 0.5rem;
		font-size: 0.875rem;
		font-weight: 500;
		transition: background-color 0.2s;
	}
	
	.login-btn:hover {
		background: #2563eb;
	}

	h1 {
		font-size: 2.5rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.5rem 0;
	}

	header p {
		font-size: 1.1rem;
		color: #64748b;
		margin: 0;
	}

	section {
		margin-bottom: 3rem;
	}

	h2 {
		font-size: 1.5rem;
		font-weight: 600;
		color: #1e293b;
		margin: 0 0 1rem 0;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.status-card {
		background: white;
		border-radius: 0.75rem;
		border-left: 4px solid;
		padding: 1.5rem;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
		margin-bottom: 1rem;
	}

	.status-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
	}

	.status-icon {
		font-size: 1.25rem;
	}

	.status-header h3 {
		margin: 0;
		font-size: 1.1rem;
		font-weight: 600;
	}

	.status-message {
		margin: 0.5rem 0;
		color: #475569;
	}

	small {
		color: #94a3b8;
		font-family: monospace;
	}

	.message {
		padding: 1rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
		font-weight: 500;
	}

	.message-success {
		background-color: #dcfce7;
		color: #166534;
		border: 1px solid #bbf7d0;
	}

	.message-error {
		background-color: #fef2f2;
		color: #dc2626;
		border: 1px solid #fecaca;
	}

	.primary-btn {
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 0.5rem;
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.primary-btn:hover {
		background: #2563eb;
	}

	.form-card {
		background: white;
		border-radius: 0.75rem;
		padding: 1.5rem;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
		margin-bottom: 1.5rem;
		border: 1px solid #e2e8f0;
	}

	.form-card h3 {
		margin: 0 0 1rem 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #1e293b;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	label {
		display: block;
		margin-bottom: 0.25rem;
		font-weight: 500;
		color: #374151;
	}

	input {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		transition: border-color 0.2s;
	}

	input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1);
	}

	input:disabled {
		background-color: #f9fafb;
		color: #6b7280;
	}

	.form-actions {
		margin-top: 1.5rem;
	}

	.submit-btn {
		background: #059669;
		color: white;
		border: none;
		border-radius: 0.5rem;
		padding: 0.75rem 1.5rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.submit-btn:hover:not(:disabled) {
		background: #047857;
	}

	.submit-btn:disabled {
		background: #9ca3af;
		cursor: not-allowed;
	}

	.users-list {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
		border: 1px solid #e2e8f0;
		overflow: hidden;
	}

	.loading, .empty-state {
		padding: 2rem;
		text-align: center;
		color: #6b7280;
	}

	.users-table {
		width: 100%;
	}

	.table-header {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		background: #f8fafc;
		border-bottom: 1px solid #e2e8f0;
		font-weight: 600;
		color: #374151;
	}

	.table-row {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		border-bottom: 1px solid #f1f5f9;
	}

	.table-row:last-child {
		border-bottom: none;
	}

	.table-row:hover {
		background: #f8fafc;
	}

	.table-cell {
		padding: 1rem;
		font-size: 0.875rem;
	}

	@media (max-width: 768px) {
		.section-header {
			flex-direction: column;
			gap: 1rem;
			align-items: stretch;
		}

		.table-header, .table-row {
			grid-template-columns: 1fr;
		}

		.table-cell {
			padding: 0.5rem 1rem;
		}

		.table-header .table-cell {
			display: none;
		}

		.table-row .table-cell:before {
			content: attr(data-label);
			font-weight: 600;
			margin-right: 0.5rem;
			color: #6b7280;
		}
	}
</style>