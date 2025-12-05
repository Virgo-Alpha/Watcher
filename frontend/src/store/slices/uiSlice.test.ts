import uiReducer, {
  setLeftPanelWidth,
  setMiddlePanelWidth,
  setShowSetupWizard,
  setKeyboardShortcutsEnabled,
  setAutoMarkReadOnScroll,
  toggleFolder,
  collapseFolder,
  expandFolder,
} from './uiSlice';
import { UIState } from '../../types';

describe('uiSlice', () => {
  const initialState: UIState = {
    leftPanelWidth: 250,
    middlePanelWidth: 400,
    showSetupWizard: false,
    keyboardShortcutsEnabled: true,
    autoMarkReadOnScroll: false,
    collapsedFolders: [],
  };

  it('should return the initial state', () => {
    expect(uiReducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  describe('Panel Width Actions', () => {
    it('should handle setLeftPanelWidth', () => {
      const actual = uiReducer(initialState, setLeftPanelWidth(300));
      expect(actual.leftPanelWidth).toBe(300);
    });

    it('should handle setMiddlePanelWidth', () => {
      const actual = uiReducer(initialState, setMiddlePanelWidth(500));
      expect(actual.middlePanelWidth).toBe(500);
    });
  });

  describe('UI State Actions', () => {
    it('should handle setShowSetupWizard', () => {
      const actual = uiReducer(initialState, setShowSetupWizard(true));
      expect(actual.showSetupWizard).toBe(true);
    });

    it('should handle setKeyboardShortcutsEnabled', () => {
      const actual = uiReducer(initialState, setKeyboardShortcutsEnabled(false));
      expect(actual.keyboardShortcutsEnabled).toBe(false);
    });

    it('should handle setAutoMarkReadOnScroll', () => {
      const actual = uiReducer(initialState, setAutoMarkReadOnScroll(true));
      expect(actual.autoMarkReadOnScroll).toBe(true);
    });
  });

  describe('Folder Collapse Actions', () => {
    describe('toggleFolder', () => {
      it('should add folder to collapsedFolders when not present', () => {
        const actual = uiReducer(initialState, toggleFolder('folder1'));
        expect(actual.collapsedFolders).toEqual(['folder1']);
      });

      it('should remove folder from collapsedFolders when present', () => {
        const stateWithCollapsed: UIState = {
          ...initialState,
          collapsedFolders: ['folder1', 'folder2'],
        };
        const actual = uiReducer(stateWithCollapsed, toggleFolder('folder1'));
        expect(actual.collapsedFolders).toEqual(['folder2']);
      });

      it('should toggle multiple folders independently', () => {
        let state = uiReducer(initialState, toggleFolder('folder1'));
        state = uiReducer(state, toggleFolder('folder2'));
        expect(state.collapsedFolders).toEqual(['folder1', 'folder2']);
        
        state = uiReducer(state, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder2']);
      });

      it('should handle toggling the same folder multiple times', () => {
        let state = uiReducer(initialState, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder1']);
        
        state = uiReducer(state, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual([]);
        
        state = uiReducer(state, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder1']);
      });
    });

    describe('collapseFolder', () => {
      it('should add folder to collapsedFolders when not present', () => {
        const actual = uiReducer(initialState, collapseFolder('folder1'));
        expect(actual.collapsedFolders).toEqual(['folder1']);
      });

      it('should not duplicate folder in collapsedFolders when already present', () => {
        const stateWithCollapsed: UIState = {
          ...initialState,
          collapsedFolders: ['folder1'],
        };
        const actual = uiReducer(stateWithCollapsed, collapseFolder('folder1'));
        expect(actual.collapsedFolders).toEqual(['folder1']);
      });

      it('should add multiple folders to collapsedFolders', () => {
        let state = uiReducer(initialState, collapseFolder('folder1'));
        state = uiReducer(state, collapseFolder('folder2'));
        state = uiReducer(state, collapseFolder('folder3'));
        expect(state.collapsedFolders).toEqual(['folder1', 'folder2', 'folder3']);
      });

      it('should handle collapsing already collapsed folders idempotently', () => {
        let state = uiReducer(initialState, collapseFolder('folder1'));
        state = uiReducer(state, collapseFolder('folder1'));
        state = uiReducer(state, collapseFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder1']);
      });

      it('should preserve existing collapsed folders when adding new ones', () => {
        const stateWithCollapsed: UIState = {
          ...initialState,
          collapsedFolders: ['folder1', 'folder2'],
        };
        const actual = uiReducer(stateWithCollapsed, collapseFolder('folder3'));
        expect(actual.collapsedFolders).toEqual(['folder1', 'folder2', 'folder3']);
      });
    });

    describe('expandFolder', () => {
      it('should remove folder from collapsedFolders when present', () => {
        const stateWithCollapsed: UIState = {
          ...initialState,
          collapsedFolders: ['folder1', 'folder2'],
        };
        const actual = uiReducer(stateWithCollapsed, expandFolder('folder1'));
        expect(actual.collapsedFolders).toEqual(['folder2']);
      });

      it('should handle expanding non-collapsed folder gracefully', () => {
        const actual = uiReducer(initialState, expandFolder('folder1'));
        expect(actual.collapsedFolders).toEqual([]);
      });

      it('should expand multiple folders independently', () => {
        const stateWithCollapsed: UIState = {
          ...initialState,
          collapsedFolders: ['folder1', 'folder2', 'folder3'],
        };
        let state = uiReducer(stateWithCollapsed, expandFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder2', 'folder3']);
        
        state = uiReducer(state, expandFolder('folder3'));
        expect(state.collapsedFolders).toEqual(['folder2']);
      });

      it('should handle expanding all folders', () => {
        const stateWithCollapsed: UIState = {
          ...initialState,
          collapsedFolders: ['folder1', 'folder2'],
        };
        let state = uiReducer(stateWithCollapsed, expandFolder('folder1'));
        state = uiReducer(state, expandFolder('folder2'));
        expect(state.collapsedFolders).toEqual([]);
      });
    });

    describe('Folder Actions Integration', () => {
      it('should work correctly when combining collapse and expand actions', () => {
        let state = uiReducer(initialState, collapseFolder('folder1'));
        state = uiReducer(state, collapseFolder('folder2'));
        expect(state.collapsedFolders).toEqual(['folder1', 'folder2']);
        
        state = uiReducer(state, expandFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder2']);
        
        state = uiReducer(state, collapseFolder('folder3'));
        expect(state.collapsedFolders).toEqual(['folder2', 'folder3']);
      });

      it('should work correctly when combining toggle and collapse actions', () => {
        let state = uiReducer(initialState, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder1']);
        
        state = uiReducer(state, collapseFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder1']);
        
        state = uiReducer(state, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual([]);
      });

      it('should work correctly when combining toggle and expand actions', () => {
        let state = uiReducer(initialState, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder1']);
        
        state = uiReducer(state, expandFolder('folder1'));
        expect(state.collapsedFolders).toEqual([]);
        
        state = uiReducer(state, toggleFolder('folder1'));
        expect(state.collapsedFolders).toEqual(['folder1']);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty folder IDs', () => {
      const actual = uiReducer(initialState, collapseFolder(''));
      expect(actual.collapsedFolders).toEqual(['']);
    });

    it('should handle numeric folder IDs as strings', () => {
      const actual = uiReducer(initialState, collapseFolder('123'));
      expect(actual.collapsedFolders).toEqual(['123']);
    });

    it('should handle special characters in folder IDs', () => {
      const actual = uiReducer(initialState, collapseFolder('folder-with-dashes_and_underscores'));
      expect(actual.collapsedFolders).toEqual(['folder-with-dashes_and_underscores']);
    });

    it('should maintain state immutability', () => {
      const state = { ...initialState };
      const newState = uiReducer(state, collapseFolder('folder1'));
      
      expect(state.collapsedFolders).toEqual([]);
      expect(newState.collapsedFolders).toEqual(['folder1']);
      expect(state).not.toBe(newState);
    });
  });
});
