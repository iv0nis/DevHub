/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // API routes configuration
  api: {
    bodyParser: {
      sizeLimit: '1mb',
    },
    responseLimit: '8mb',
  },

  // Custom webpack config for Python integration
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Server-side only packages
      config.externals.push('python-shell')
    }
    return config
  },

  // Environment variables
  env: {
    DEVHUB_PROJECT_PATH: process.env.DEVHUB_PROJECT_PATH || process.cwd(),
    PYTHON_PATH: process.env.PYTHON_PATH || 'python3'
  }
}

module.exports = nextConfig