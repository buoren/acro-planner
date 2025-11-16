import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

/**
 * Cross-platform secure storage utility
 * Uses SecureStore on native platforms and localStorage on web
 */
class Storage {
  async setItem(key: string, value: string): Promise<void> {
    if (Platform.OS === 'web') {
      // Use localStorage for web
      try {
        localStorage.setItem(key, value);
      } catch (error) {
        console.error('Failed to store item in localStorage:', error);
        throw new Error('Storage not available');
      }
    } else {
      // Use SecureStore for native platforms
      try {
        await SecureStore.setItemAsync(key, value);
      } catch (error) {
        console.error('Failed to store item in SecureStore:', error);
        throw new Error('Secure storage not available');
      }
    }
  }

  async getItem(key: string): Promise<string | null> {
    if (Platform.OS === 'web') {
      // Use localStorage for web
      try {
        return localStorage.getItem(key);
      } catch (error) {
        console.error('Failed to get item from localStorage:', error);
        return null;
      }
    } else {
      // Use SecureStore for native platforms
      try {
        return await SecureStore.getItemAsync(key);
      } catch (error) {
        console.error('Failed to get item from SecureStore:', error);
        return null;
      }
    }
  }

  async deleteItem(key: string): Promise<void> {
    if (Platform.OS === 'web') {
      // Use localStorage for web
      try {
        localStorage.removeItem(key);
      } catch (error) {
        console.error('Failed to delete item from localStorage:', error);
        throw new Error('Storage not available');
      }
    } else {
      // Use SecureStore for native platforms
      try {
        await SecureStore.deleteItemAsync(key);
      } catch (error) {
        console.error('Failed to delete item from SecureStore:', error);
        throw new Error('Secure storage not available');
      }
    }
  }
}

export const storage = new Storage();