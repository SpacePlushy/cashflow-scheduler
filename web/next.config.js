/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Using API route handler in app/api/[...path]/route.ts for proxying upstream API with bypass token
}

module.exports = nextConfig
