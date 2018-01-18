
if [ $# -eq 0 ]
then
    echo "Missing text file path. Please enter: ./run.sh text_file_path"
else
    python main.py "$1"
fi

