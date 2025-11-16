import Constants from 'expo-constants';

interface Environment {
  API_BASE_URL: string;
  API_TIMEOUT: number;
  ENVIRONMENT: 'development' | 'production';
}

const DEV_ENV: Environment = {
  API_BASE_URL: 'https://acro-planner-backend-733697808355.us-central1.run.app',
  API_TIMEOUT: 30000,
  ENVIRONMENT: 'development',
};

const PROD_ENV: Environment = {
  API_BASE_URL: 'https://acro-planner-backend-733697808355.us-central1.run.app',
  API_TIMEOUT: 30000,
  ENVIRONMENT: 'production',
};

const getEnvironment = (): Environment => {
  if (__DEV__) {
    return DEV_ENV;
  }
  return PROD_ENV;
};

export const ENV = getEnvironment();