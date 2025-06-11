module.exports = {
  parser: 'typescript-eslint',
  plugins: ['typescript-eslint'],
  extends: [
    'eslint:recommended',
    'plugin:typescript-eslint/recommended',
  ],
  env: {
    browser: true,
    es2021: true,
  },
};
