# MVSEP-MDX23-music-separation-model
Model for [Sound demixing challenge 2023: Music Demixing Track - MDX'23](https://www.aicrowd.com/challenges/sound-demixing-challenge-2023). Model perform separation of music into 4 stems "bass", "drums", "vocals", "other". Model won 3rd place in challenge (Leaderboard C).

Model based on [Demucs4](https://github.com/facebookresearch/demucs), [MDX](https://github.com/kuielab/mdx-net) neural net architectures and some MDX weights from [Ultimate Vocal Remover](https://github.com/Anjok07/ultimatevocalremovergui) project (thanks [Kimberley Jensen](https://github.com/KimberleyJensen) for great high quality vocal models). Thanks [@Ma5onic](https://github.com/Ma5onic) for web UI & helping with dataset augmentation techniques. Brought to you by [MVSep.com](https://mvsep.com).
## Usage

```
python gui_modern.py
```

## Screenshot
![alt text](image.png)

With this command audios with names "mixture1.wav" and "mixture2.wav" will be processed and results will be stored in `./results/` folder in WAV format.

### Notes
* If you have not enough GPU memory you can use CPU, but it will be slow. Additionally you can use single ONNX, but it will decrease quality a little bit. Also reduce of chunk size can help.
* In current revision code requires less GPU memory, but it process multiple files slower. If you want old fast method use argument. It will require > 11 GB of GPU memory, but will work faster.

## Quality comparison

Quality comparison with best separation models performed on [MultiSong Dataset](https://mvsep.com/quality_checker/leaderboard2.php?sort=bass). 

| Algorithm     | SDR bass  | SDR drums  | SDR other  | SDR vocals  | SDR instrumental  |
| ------------- |:---------:|:----------:|:----------:|:----------:|:------------------:|
| MVSEP MDX23   | 12.5034   | 11.6870    | 6.5378     |  9.5138    | 15.8213            |
| Demucs HT 4   | 12.1006   | 11.3037    | 5.7728     |  8.3555    | 13.9902            |
| Demucs 3      | 10.6947   | 10.2744    | 5.3580     |  8.1335    | 14.4409            |
| MDX B         | ---       | ----       | ---        |  8.5118    | 14.8192            |
