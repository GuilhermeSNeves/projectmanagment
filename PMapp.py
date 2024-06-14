import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import plotly.express as px
import pandas as pd
from datetime import date, datetime

def main():
    st.set_page_config(
        page_title="Project Management",
        page_icon="📖",
        layout="wide"
    )

    ## Database setup
    Base = declarative_base()
    engine = create_engine('sqlite:///project_management.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    ## Project class
    class Project(Base):
        __tablename__ = 'projects'
        id = Column(Integer, primary_key=True)
        name = Column(String(100), nullable=False)
        description = Column(String(200), nullable=True)
        start_date = Column(Date, nullable=False)
        end_date = Column(Date, nullable=False)
        subfolders = relationship('SubFolder', backref='project', cascade='all, delete-orphan')

    ## SubFolder class
    class SubFolder(Base):
        __tablename__ = 'subfolders'
        id = Column(Integer, primary_key=True)
        project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
        name = Column(String(100), nullable=False)
        tasks = relationship('Task', backref='subfolder', cascade='all, delete-orphan')

    ## Task class
    class Task(Base):
        __tablename__ = 'tasks'
        id = Column(Integer, primary_key=True)
        subfolder_id = Column(Integer, ForeignKey('subfolders.id'), nullable=False)
        name = Column(String(100), nullable=False)
        assignee = Column(String(100), nullable=False)
        start_date = Column(Date, nullable=False)
        end_date = Column(Date, nullable=False)
        status = Column(String(20), default='To Start')
        archived = Column(Integer, default=0)  # 0 for active, 1 for archived
        visible_in_clipboard = Column(Integer, default=1)  # 1 for visible, 0 for not visible

    ## Note Class
    class Note(Base):
        __tablename__ = 'notes'
        id = Column(Integer, primary_key=True)
        content = Column(String(500), nullable=False)
        assignee = Column(String(100), nullable=False)
        created_at = Column(DateTime, default=datetime.now)

    Base.metadata.create_all(engine)

    ## App
    st.sidebar.title('Navigation')
    page = st.sidebar.radio('Select a page:', ['Project', 'SubFolder', 'Task', 'Gantt Chart', 'Team Clipboard', 'Project Overview', 'Notes'])

    def add_project(name, description, start_date, end_date):
        new_project = Project(name=name, description=description, start_date=start_date, end_date=end_date)
        session.add(new_project)
        session.commit()

    def add_subfolder(name, project_id):
        new_subfolder = SubFolder(name=name, project_id=project_id)
        session.add(new_subfolder)
        session.commit()

    def add_task(name, subfolder_id, assignee, start_date, end_date, status='To Start'):
        new_task = Task(name=name, subfolder_id=subfolder_id, assignee=assignee, start_date=start_date, end_date=end_date, status=status)
        session.add(new_task)
        session.commit()

    def delete_project(project_id):
        project = session.query(Project).get(project_id)
        if project:
            session.delete(project)
            session.commit()

    def delete_subfolder(subfolder_id):
        subfolder = session.query(SubFolder).get(subfolder_id)
        if subfolder:
            session.delete(subfolder)
            session.commit()

    def delete_task(task_id, archive=False):
        task = session.query(Task).get(task_id)
        if task:
            if archive:
                task.visible_in_clipboard = 0  # Mark as not visible in clipboard
                session.commit()
            else:
                session.delete(task)
                session.commit()

    def update_task_status(task_id, new_status):
        task = session.query(Task).get(task_id)
        if task:
            task.status = new_status
            if new_status == 'Finished':
                task.visible_in_clipboard = 0  # Mark as not visible in clipboard when finished
            else:
                task.visible_in_clipboard = 1  # Ensure visibility for other statuses
            session.commit()

    def get_status_color(status):
        if status == 'To Start':
            return '#FFFFFF'  # White
        if status == 'Working':
            return '#FFD700'  # Yellow
        elif status == 'Stuck':
            return '#FF4500'  # Orange Red
        elif status == 'Finished':
            return '#32CD32'  # Lime Green
        return '#FFFFFF'  # Default White
    
    def get_status_color2(status):
        if status == 'To Start':
            return 'background-color: white; color: black;'
        elif status == 'Working':
            return 'background-color: yellow; color: black;'
        elif status == 'Stuck':
            return 'background-color: red; color: white;'
        elif status == 'Finished':
            return 'background-color: green; color: white;'
        return ''

    def save_note(note_content, assignee):
        new_note = Note(content=note_content, assignee=assignee)
        session.add(new_note)
        session.commit()
    
    def delete_note(note_id):
        note = session.query(Note).get(note_id)
        if note:
            session.delete(note)
            session.commit()

    def display_notes(assignee):
        st.subheader(f'Notes from {assignee}:')
        notes = session.query(Note).filter_by(assignee=assignee).all()
        if notes:
            for note in notes:
                st.write(f"{note.content} \n\nCreated At: {note.created_at}")
                if st.button(f'Delete Note {note.id}'):
                    delete_note(note.id)
                    st.success('Note deleted successfully.')
        else:
            st.write('No notes available.')

    ## Project Page
    if page == 'Project':
        st.title('Add New Project')
        project_name = st.text_input('Project Name')
        project_description = st.text_input('Description')
        start_date = st.date_input('Start Date', date.today())
        end_date = st.date_input('End Date', date.today())
        if st.button('Add Project'):
            add_project(project_name, project_description, start_date, end_date)
            st.success('Project added successfully!')

        st.title('Delete Project')
        projects = session.query(Project).all()
        project_options = {project.name: project.id for project in projects}
        selected_project = st.selectbox('Select Project to Delete', options=list(project_options.keys()))
        if st.button('Delete Project'):
            delete_project(project_options[selected_project])
            st.success('Project deleted successfully!')

    ## SubFolder Management Page
    if page == 'SubFolder':
        st.title('Add New SubFolder')
        project_options = {project.name: project.id for project in session.query(Project).all()}
        selected_project = st.selectbox('Select Project', options=list(project_options.keys()))
        subfolder_name = st.text_input('SubFolder Name')
        if st.button('Add SubFolder'):
            add_subfolder(subfolder_name, project_options[selected_project])
            st.success('SubFolder added successfully!')

        st.title('Delete SubFolder')
        selected_project = st.selectbox('Select Project for SubFolder', options=list(project_options.keys()), key='delete_subfolder_project')
        
        if selected_project:
            subfolders = session.query(SubFolder).filter_by(project_id=project_options[selected_project]).all()
            subfolder_options = {subfolder.name: subfolder.id for subfolder in subfolders}
            selected_subfolder = st.selectbox('Select SubFolder to Delete', options=list(subfolder_options.keys()), key='delete_subfolder')
            if st.button('Delete SubFolder'):
                delete_subfolder(subfolder_options[selected_subfolder])
                st.success('SubFolder deleted successfully!')

    ## Task Management page
    if page == 'Task':
        st.title('Add New Task')
        task_name = st.text_input('Task Name')
        project_options = {project.name: project.id for project in session.query(Project).all()}
        selected_project = st.selectbox('Select Project', options=list(project_options.keys()))
        if selected_project:
            subfolder_options = {subfolder.name: subfolder.id for subfolder in session.query(SubFolder).filter_by(project_id=project_options[selected_project]).all()}
            selected_subfolder = st.selectbox('Select SubFolder', options=list(subfolder_options.keys()))
            assignee = st.text_input('Assignee')
            start_date = st.date_input('Start Date', date.today())
            end_date = st.date_input('End Date', date.today())
            if st.button('Add Task'):
                add_task(task_name, subfolder_options[selected_subfolder], assignee, start_date, end_date)
                st.success('Task added successfully!')

        st.title('Delete Task')
        selected_project = st.selectbox('Select Project', options=list(project_options.keys()), key='delete_project')
        
        if selected_project:
            subfolders = session.query(SubFolder).filter_by(project_id=project_options[selected_project]).all()
            subfolder_options = {subfolder.name: subfolder.id for subfolder in subfolders}
            selected_subfolder = st.selectbox('Select SubFolder', options=list(subfolder_options.keys()), key='delete_subfolder_task')
            
            if selected_subfolder:
                tasks = session.query(Task).filter_by(subfolder_id=subfolder_options[selected_subfolder]).all()
                task_names = list(set([task.name for task in tasks]))
                selected_task_name = st.selectbox('Select Task', options=task_names, key='delete_task_name')
                
                if selected_task_name:
                    assignee_options = [task.assignee for task in tasks if task.name == selected_task_name]
                    selected_assignee = st.selectbox('Select Assignee', options=assignee_options, key='delete_task_assignee')
                    
                    if st.button('Delete Task'):
                        task_to_delete = session.query(Task).filter_by(name=selected_task_name, subfolder_id=subfolder_options[selected_subfolder], assignee=selected_assignee).first()
                        if task_to_delete:
                            delete_task(task_to_delete.id)
                            st.success('Task deleted successfully!')

    ## Gantt Chart Page
    if page == 'Gantt Chart':
        st.title('Gantt Chart')
        tasks = session.query(Task).all()
        #subfolders = session.query(SubFolder).all()
        projects = session.query(Project).all()
        
        if tasks:
            task_data = [{
                'Task': f"{session.query(SubFolder).get(task.subfolder_id).name} - {task.name}",
                'Start': task.start_date,
                'Finish': task.end_date,
                'Resource': task.assignee
            } for task in tasks]

            #subfolder_data = [{
             #   'Task': f"{subfolder.name}",
              #  'Start': min([task.start_date for task in subfolder.tasks]),
               # 'Finish': max([task.end_date for task in subfolder.tasks]),
                #'Resource': 'SubFolder'
            #} for subfolder in subfolders]

            project_data = [{
                'Task': project.name,
                'Start': project.start_date,
                'Finish': project.end_date,
                'Resource': 'Project'
            } for project in projects]

            df = pd.DataFrame(task_data + project_data) #(task_data + subfolder_data + project_data)

            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource", title="Gantt Chart")
            fig.update_layout(height=500, width=900)
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig)
            
    ## Team Clipboard Page
    if page == 'Team Clipboard':
        st.title('Team Clipboard')
        team_tasks = session.query(Task).filter_by(visible_in_clipboard=1).all()  # Only tasks visible in clipboard
        if team_tasks:
            tasks_by_assignee = {}
            for task in team_tasks:
                if task.assignee not in tasks_by_assignee:
                    tasks_by_assignee[task.assignee] = []
                tasks_by_assignee[task.assignee].append(task)

            assignees = list(tasks_by_assignee.keys())
            columns = st.columns(len(assignees))

            for i, assignee in enumerate(assignees):
                with columns[i]:
                    st.subheader(assignee)
                    for task in tasks_by_assignee[assignee]:
                        task_color = get_status_color(task.status)
                        st.markdown(f"<div style='background-color: {task_color}; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
                        st.markdown(f"**Task:**  {task.name}")
                        st.write(f"**SubFolder:**  {session.query(SubFolder).get(task.subfolder_id).name}")
                        st.write(f"**Duration:**  {task.start_date} to {task.end_date}")
                        status_options = ['To Start', 'Working', 'Stuck', 'Finished']
                        selected_status = st.selectbox('**Status**', status_options, index=status_options.index(task.status), key=f"{task.id}_status")
                        if st.button('Update Status', key=f"{task.id}_update"):
                            update_task_status(task.id, selected_status)
                            st.success(f"Status of '{task.name}' updated to '{selected_status}'")
                        if st.button('Delete Task', key=f"{task.id}_delete"):
                            delete_task(task.id, archive=True)
                            st.success('Task removed from Team Clipboard successfully!')
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.write("---")

    ## Project Overview
    if page == 'Project Overview':
        st.title('Project Overview')

        projects = session.query(Project).all()
        for project in projects:
            st.markdown(f"## Project: {project.name}")
            st.markdown(f"*Description:* {project.description}")

            subfolders = session.query(SubFolder).filter_by(project_id=project.id).all()

            if subfolders:
                for subfolder in subfolders:
                    st.markdown(f"### SubFolder: {subfolder.name}")

                    tasks = session.query(Task).filter_by(subfolder_id=subfolder.id).all()  # Include all tasks
                    if tasks:
                        task_data = []
                        for task in tasks:
                            task_data.append({
                                'Task': task.name,
                                'Assignee': task.assignee,
                                'Start Date': task.start_date,
                                'End Date': task.end_date,
                                'Status': task.status
                            })

                        df = pd.DataFrame(task_data)

                        def apply_status_color(val):
                            return [get_status_color2(v) for v in val]

                        styled_df = df.style.apply(apply_status_color, subset=['Status'])
                        st.table(styled_df)
                    else:
                        st.markdown("No tasks found for this subfolder.")
            else:
                st.markdown("No subfolders found for this project.")
            st.markdown("---")

    ## Notes Page
    if page == 'Notes':
        st.title('Notes Page')
        ## Fetch unique assignees from Task class
        assignees = session.query(Task.assignee).distinct().all()
        assignee_options = [assignee[0] for assignee in assignees]

        for assignee in assignee_options:
            display_notes(assignee)  ## Pass the assignee when calling display_notes

        st.subheader('Add New Note')
        note_content = st.text_area('Note Content')
        assignee = st.selectbox('Assignee', options=assignee_options)
        if st.button('Save Note'):
            save_note(note_content, assignee)
            st.success('Note saved successfully!')

if __name__ == '__main__':
    main()
