import React, { useState, useEffect } from "react";
import { firestorage } from "../../helpers/firebase";
import { useHistory, useParams } from "react-router-dom";
import { makeStyles } from '@material-ui/core/styles';
import { createSimulation, updateSimulation, getSimulation } from '../../helpers/api';
import Button from "@material-ui/core/Button";
import FormControl from "@material-ui/core/FormControl";
import InputLabel from "@material-ui/core/InputLabel";
import Select from "@material-ui/core/Select";
import TextField from '@material-ui/core/TextField';
import CircularProgress from '@material-ui/core/CircularProgress';

const useStyles = makeStyles(() => ({
  root: {
    flexGrow: 1
  },
  form: {
    display: 'flex',
    flexFlow: 'column'
  },
  formControl: {
    marginBottom: 16,
  },
  formSelect: {
    paddingTop: 16
  },
  chooseFileButton: {
    minWidth: 180,
    marginBottom: 16
  },
  chooseFileLink: {
    color: '#ff6600',
    marginLeft: 16
  },
  image: {
    maxWidth: 400,
    maxHeight: 400,
    marginBottom: 16
  },
  submit: {
    marginTop: 8,
    marginBottom: 8
  }
}));

const FileInput = ({ id, text, url, accept, onChange, uploadProgress }) => {
  const classes = useStyles();

  return (
    <div>
      <input
        accept={accept}
        style={{ display: 'none' }}
        id={id}
        type="file"
        onChange={onChange}
      />
      <label htmlFor={id}>
        <Button 
          variant="outlined" 
          component="span" 
          className={classes.chooseFileButton}
          disabled={!!uploadProgress}
        >
          {uploadProgress ? `${uploadProgress}%` : `${text}`}
        </Button>
      </label>
      {url && 
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className={classes.chooseFileLink}
        >
          Download
        </a>}
    </div>
  )
}


const SimulationCreate = () => {
  const classes = useStyles();
  const { simulationId } = useParams();
  const history = useHistory();
  const [simulation, setSimulation] = useState({
    runner: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [uploadImageProgress, setUploadImageProgress] = useState(null);
  const [uploadConfigProgress, setUploadConfigProgress] = useState(null);
  const [uploadTopologyProgress, setUploadTopologyProgress] = useState(null);
  const [uploadTrajectoryProgress, setUploadTrajectoryProgress] = useState(null);
  const [uploadRenderingProgress, setUploadRenderingProgress] = useState(null);
  const [loading, setLoading] = useState(!!simulationId);

  useEffect(() => {
    (async () => {
      if (simulationId) {
        try {
          const result = await getSimulation(simulationId);
          setSimulation(result);
        } catch (e) {
          console.log(e);
        }
        setLoading(false);
      };
    })();
  }, []);

  const random_six_digits = () => {
    return Math.floor(100000 + Math.random() * 900000);
  }

  const uploadFile = (e, onUpdateProgress, onDownloadUrl) => {
    onUpdateProgress(0);
    const f = e.target.files[0];
    const uploadRef = firestorage().ref(`/simulations/${random_six_digits()}_${f.name}`);
    uploadRef.put(f).on('state_changed', snapshot => {
      const progress = Math.round(100 * snapshot.bytesTransferred / snapshot.totalBytes);
      onUpdateProgress(progress);
    }, e => {
      console.log(e);
      onUpdateProgress(null);
    }, () => {
      uploadRef.getDownloadURL().then(url => {
        onDownloadUrl(url)
        onUpdateProgress(null);
      });
    });
  }

  const onChangeDescription = e => {
    setSimulation({...simulation, description: e.currentTarget.value});
  }

  const onChangeName = e => {
    setSimulation({...simulation, name: e.currentTarget.value});
  }

  const onChangeAuthor = e => {
    setSimulation({...simulation, author: e.currentTarget.value});
  }

  const onChangeCitation = e => {
    setSimulation({...simulation, citation: e.currentTarget.value});
  }

  const onChangeRunner = e => {
    setSimulation({...simulation, runner: e.currentTarget.value});
  }

  const onChangeImage = e => {
    uploadFile(e, setUploadImageProgress, url => simulation.image_url = url);
  }

  const onChangeConfig = e => {
    uploadFile(e, setUploadConfigProgress, url => simulation.config_url = url);
  }

  const onChangeTopology = e => {
    uploadFile(e, setUploadTopologyProgress, url => simulation.topology_url = url);
  }

  const onChangeTrajectory = e => {
    uploadFile(e, setUploadTrajectoryProgress, url => simulation.trajectory_url = url);
  }

  const onChangeRendering = e => {
    uploadFile(e, setUploadRenderingProgress, url => simulation.rendering_url = url);
  }

  const onSubmit = async e => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (simulationId) {
        await updateSimulation(simulation);
      } else {
        await createSimulation(simulation);
      }
      history.push('/simulations');
    } catch (e) {
      console.log(e);
      setSubmitting(false);
    }
  };
  
  const onCancel = () => {
    history.push('/simulations');
  };

  return (
    loading ?
      <CircularProgress/>
    :
    <div className={classes.root}>
      <form noValidate className={classes.form}>
        <TextField
          variant="outlined"
          label="Name"
          defaultValue={simulation.name}
          onChange={onChangeName}
          className={classes.formControl}
        />
        <TextField
          variant="outlined"
          label="Description"
          defaultValue={simulation.description}
          onChange={onChangeDescription}
          className={classes.formControl}
        />
        <TextField
          variant="outlined"
          label="Author"
          defaultValue={simulation.author}
          onChange={onChangeAuthor}
          className={classes.formControl}
        />
        <TextField
          variant="outlined"
          label="Citation"
          defaultValue={simulation.citation}
          onChange={onChangeCitation}
          className={classes.formControl}
        />
        {simulation.image_url && 
          <img 
            src={simulation.image_url} 
            className={classes.image} 
            alt={simulation.name}
          />
        }
        <FileInput 
          id="image-input"
          text="Choose thumbnail"
          accept="image/*"
          onChange={onChangeImage}
          uploadProgress={uploadImageProgress}
        />
        <FormControl variant="outlined" className={classes.formControl}>
          <InputLabel>Runner</InputLabel>
          <Select
            native
            defaultValue={simulation.runner}
            onChange={onChangeRunner}
            label="Runner"
          >
            <option disabled value=''></option>
            <option value='ase'>ASE</option>
            <option value='omm'>OMM</option>
            <option value='static'>Static</option>
            <option value='topology'>Topology</option>
          </Select>
        </FormControl>
        {(simulation.runner === 'ase' || simulation.runner === 'omm') &&
          <FileInput 
            id="config-input"
            text="Choose config"
            url={simulation.config_url}
            accept="*/*"
            onChange={onChangeConfig}
            uploadProgress={uploadConfigProgress}
          />
        }
        {(simulation.runner === 'topology' || simulation.runner === 'static') &&
          <FileInput 
            id="topology-input"
            text="Choose topology"
            url={simulation.topology_url}
            accept="*/*"
            onChange={onChangeTopology}
            uploadProgress={uploadTopologyProgress}
          />
        }
        {simulation.runner === 'topology' &&
          <FileInput 
            id="trajectory-input"
            text="Choose trajectory"
            url={simulation.trajectory_url}
            accept="*/*"
            onChange={onChangeTrajectory}
            uploadProgress={uploadTrajectoryProgress}
          />
        }
        {false &&
          <FileInput 
            id="rendering-input"
            text="Choose rendering"
            url={simulation.rendering_url}
            accept="*/*"
            onChange={onChangeRendering}
            uploadProgress={uploadRenderingProgress}
          />
        }
        <Button 
          type="submit"
          color="primary"
          variant="contained"
          onClick={onSubmit}
          className={classes.submit}
          disabled={submitting || !!uploadImageProgress || !!uploadConfigProgress || !!uploadTopologyProgress}
        >
          {simulationId ? 'Save' : 'Add'}
        </Button>
        <Button 
          variant="outlined"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>
      </form>
    </div>
  )
}

export default SimulationCreate;