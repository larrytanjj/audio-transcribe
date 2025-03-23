import { useState, useEffect } from 'react';
import './App.css'
import { Alert, Button, ConfigProvider, Spin, Table, TableProps, theme } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import { message, Upload, Input } from 'antd';
import axios from 'axios';
import { SearchProps } from 'antd/es/input';

function App() {

  const [transcriptions, setTranscriptions] = useState([]);
  const [fetching, setFeteching] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [online, setOnline] = useState(false);

  interface TranscriptDataType {
    id: string;
    original_filename: string;
    unique_filename: number;
    transcription: string;
    tags: string[];

  }

  const { Dragger } = Upload;
  const { Search } = Input;

  const props: UploadProps = {
    name: 'audio_file',
    multiple: true,
    action: 'http://localhost:8000/transcribe',
    accept: 'audio/*',
    fileList: fileList,
    onChange(info) {
      const { status } = info.file;
      setFileList(info.fileList);
      if (status === 'done') {
        setTimeout(() => {
          setFileList([]);
        }, 1000);
        message.success(`${info.file.name} file uploaded successfully.`);
        getTranscription();
      } else if (status === 'error') {
        message.error(`${info.file.name} file upload failed.`);
      }
    },
  };

  const onSearch: SearchProps['onSearch'] = (value) => {
    searchTranscription(value);
  }


  const columns: TableProps<TranscriptDataType>['columns'] = [
    {
      title: 'Original Filename',
      dataIndex: 'original_filename',
      key: 'original_filename',
    },
    {
      title: 'Uniquie Filename',
      dataIndex: 'unique_filename',
      key: 'unique_filename',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: 'Transcription',
      dataIndex: 'transcription',
      key: 'transcription',
    },
    {
      title: '',
      dataIndex: 'id',
      key: 'id',
      render: (value) => <Button onClick={() => deleteTranscription(value)}>Delete</Button>
    },
  ];

  const getTranscription = () => {
    setFeteching(true);
    let config = {
      method: 'get',
      maxBodyLength: Infinity,
      url: 'http://localhost:8000/transcriptions'
    };

    axios.request(config)
      .then((response) => {
        setTranscriptions(response.data);
      })
      .catch((error) => {
        console.log(error);
      }).finally(() => {
        setFeteching(false);
      })
  }

  const startHealthCheck = () => {
    setInterval(() => {
      healthCheck();
    }, 3000);
  }

  const healthCheck = () => {
    let config = {
      method: 'get',
      maxBodyLength: Infinity,
      url: `http://localhost:8000/health`
    };

    axios.request(config)
      .then((response) => {
        if (response.data.status === "healthy") {
          setOnline(true);
          getTranscription();
        }
      })
      .catch(() => {
        setOnline(false);
      })
  }

  const deleteTranscription = (id: string) => {
    setFeteching(true);
    let config = {
      method: 'delete',
      maxBodyLength: Infinity,
      url: `http://localhost:8000/transcriptions/${id}`
    };

    axios.request(config)
      .then(() => {
        getTranscription();
      })
      .catch((error) => {
        console.log(error);
      }).finally(() => {
        setFeteching(false);
      })
  }

  const searchTranscription = (query: string) => {
    setFeteching(true);
    let config = {
      method: 'get',
      maxBodyLength: Infinity,
      url: `http://localhost:8000/search?query=${query}`
    };

    axios.request(config)
      .then((response) => {
        setTranscriptions(response.data);
      })
      .catch((error) => {
        console.log(error);
      }).finally(() => {
        setFeteching(false);
      });
  }

  useEffect(() => {
    healthCheck();
    startHealthCheck();
  }, [])

  return (
    <>
      <ConfigProvider
        theme={{
          algorithm: theme.darkAlgorithm,
        }}
      >
        {online ? <Alert message="Service Online." type="success" showIcon /> : <Alert message={<span>Service Offline. Connecting... <Spin /></span>} type='error' showIcon />}
        <br />
        {online && <div>
          <Dragger {...props}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag audio file to this area to upload</p>
            <p className="ant-upload-hint">
              Support for a single or bulk audio file upload.
            </p>
          </Dragger>
          <br />
          <Search
            allowClear
            placeholder="Search audio filename"
            enterButton="Search"
            size="large"
            onSearch={onSearch}
            onClear={getTranscription}
          />
          <br />
          <br />
          <div>
            <Table loading={fetching} columns={columns} dataSource={transcriptions} />
          </div>
        </div>}
        <br />

      </ConfigProvider>

    </>
  )
}

export default App
