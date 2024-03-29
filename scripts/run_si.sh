cur_timestamp=$(date +%m%d_%H%M)
echo 'current timestamp: '$cur_timestamp

config_file=configs/self_instruct.yaml
echo "config_file: $config_file"
python demo/run.py --config $config_file | tee logs/si_$cur_timestamp 2>&1