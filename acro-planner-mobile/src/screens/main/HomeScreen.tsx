import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import ApiService from '../../services/api';

export const HomeScreen: React.FC = () => {
  const { user } = useAuth();
  const [isHealthy, setIsHealthy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [conventions, setConventions] = useState<any[]>([]);

  useEffect(() => {
    checkHealth();
    loadConventions();
  }, []);

  const checkHealth = async () => {
    const healthy = await ApiService.healthCheck();
    setIsHealthy(healthy);
  };

  const loadConventions = async () => {
    try {
      const data = await ApiService.getConventions();
      setConventions(data.slice(0, 3));
    } catch (error) {
      console.error('Failed to load conventions:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([checkHealth(), loadConventions()]);
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.welcomeText}>Welcome back,</Text>
        <Text style={styles.userName}>{user?.name || 'Guest'}</Text>
      </View>

      <View style={styles.statusCard}>
        <Text style={styles.statusLabel}>API Status:</Text>
        <View style={[styles.statusIndicator, isHealthy ? styles.healthy : styles.unhealthy]}>
          <Text style={styles.statusText}>
            {isHealthy ? 'Connected' : 'Disconnected'}
          </Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Upcoming Conventions</Text>
        {conventions.length > 0 ? (
          conventions.map((convention, index) => (
            <TouchableOpacity key={index} style={styles.conventionCard}>
              <Text style={styles.conventionName}>{convention.name}</Text>
              <Text style={styles.conventionDate}>
                {new Date(convention.start_date).toLocaleDateString()}
              </Text>
            </TouchableOpacity>
          ))
        ) : (
          <Text style={styles.emptyText}>No upcoming conventions</Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionGrid}>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>Browse Workshops</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>My Schedule</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>Conventions</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>Profile</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    paddingTop: 40,
  },
  welcomeText: {
    color: '#fff',
    fontSize: 16,
    opacity: 0.9,
  },
  userName: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 5,
  },
  statusCard: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 15,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusLabel: {
    fontSize: 16,
    color: '#666',
  },
  statusIndicator: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
  },
  healthy: {
    backgroundColor: '#4CAF50',
  },
  unhealthy: {
    backgroundColor: '#F44336',
  },
  statusText: {
    color: '#fff',
    fontWeight: '600',
  },
  section: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  conventionCard: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  conventionName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  conventionDate: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
  },
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionButton: {
    backgroundColor: '#fff',
    width: '48%',
    padding: 20,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  actionText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
});