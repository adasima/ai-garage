
/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone', // Required for Docker deployment
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'assets.coingecko.com',
            },
            {
                protocol: 'https',
                hostname: 'cdn.dexscreener.com',
            },
            {
                protocol: 'https',
                hostname: 'cryptologos.cc',
            },
        ],
    },
};

module.exports = nextConfig;
