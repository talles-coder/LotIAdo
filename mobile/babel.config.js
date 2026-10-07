module.exports = function (api) {
  api.cache(true);
  return {
    // babel-preset-expo detecta react-native-worklets instalado e injeta o plugin
    // do reanimated 4 automaticamente — não adicionar de novo aqui.
    presets: ['babel-preset-expo'],
  };
};
